import unittest
from unittest.mock import patch, MagicMock, call
import io # For capturing stdout
import sys

# Add the parent directory to sys.path to allow importing interview_system
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from interview_system import RecursiveInterviewSystem

class TestRecursiveInterviewSystem(unittest.TestCase):

    def setUp(self):
        """Set up for each test method."""
        # Mock external dependencies for RecursiveInterviewSystem instantiation
        with patch('ollama.Client') as mock_ollama_client, \
             patch('chromadb.PersistentClient') as mock_chromadb_client:
            
            # Configure the mock ChromaDB client and collections
            mock_collection = MagicMock()
            mock_chromadb_client.return_value.get_or_create_collection.return_value = mock_collection
            
            self.system = RecursiveInterviewSystem()
            
            # Assign mocks to instance if needed for specific tests, e.g.
            self.mock_ollama_client = self.system.client # This is already the mock_ollama_client
            self.mock_chromadb_client = self.system.chroma_client # This is already the mock_chromadb_client
            self.mock_host_collection = self.system.host_collection
            self.mock_expert_collection = self.system.expert_collection

    # --- Tests for clean_response ---
    def test_clean_response_with_tags_and_whitespace(self):
        text = "  <think>This is a thought.</think> Hello world!  <think>Another thought here.</think>  "
        expected = "Hello world!"
        self.assertEqual(self.system.clean_response(text), expected)

    def test_clean_response_with_only_whitespace(self):
        text = "   Lots of   spaces   here.   "
        expected = "Lots of spaces here."
        self.assertEqual(self.system.clean_response(text), expected)

    def test_clean_response_already_clean(self):
        text = "This is a clean string."
        expected = "This is a clean string."
        self.assertEqual(self.system.clean_response(text), expected)

    def test_clean_response_with_nested_and_multiple_tags(self):
        text = "<think>Outer<think>Inner</think></think>Some<think>T1</think>text<think>T2</think>here."
        expected = "Sometexthere."
        self.assertEqual(self.system.clean_response(text), expected)
        
    def test_clean_response_empty_input(self):
        text = ""
        expected = ""
        self.assertEqual(self.system.clean_response(text), expected)

    def test_clean_response_only_think_tags(self):
        text = "<think>thought one</think><think>thought two</think>"
        expected = "" # Expecting empty string as tags are removed and spaces between them collapse
        self.assertEqual(self.system.clean_response(text), expected)

    # --- Tests for perform_web_search ---
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_perform_web_search(self, mock_stdout):
        query = "test query for web search"
        expected_output = f"Placeholder search result: Recent analysis on '{query}' suggests ongoing debates, particularly around its broader implications and future trends. Some studies point to emerging complexities, while public discourse reveals a spectrum of perspectives."
        
        result = self.system.perform_web_search(query)
        self.assertEqual(result, expected_output)
        
        # Verify the printed simulation message
        self.assertIn(f"[Simulating web search for: '{query}']", mock_stdout.getvalue())

    # --- Tests for search_expert_knowledge ---
    def test_search_expert_knowledge_with_results(self):
        query = "test query"
        mock_response = {
            "documents": [["doc1 text", "doc2 text", "doc3 text"]],
            "ids": [["id1", "id2", "id3"]],
            # ... other ChromaDB fields if necessary
        }
        self.mock_expert_collection.query.return_value = mock_response
        
        expected_joined_docs = "doc1 text\n\ndoc2 text\n\ndoc3 text"
        result = self.system.search_expert_knowledge(query, n_results=3)
        
        self.assertEqual(result, expected_joined_docs)
        self.mock_expert_collection.query.assert_called_once_with(query_texts=[query], n_results=3)

    def test_search_expert_knowledge_no_documents_in_results(self):
        query = "another query"
        mock_response = {
            "documents": [[]], # Empty list of documents
            "ids": [[]],
        }
        self.mock_expert_collection.query.return_value = mock_response
        
        expected_output = ""
        result = self.system.search_expert_knowledge(query)
        
        self.assertEqual(result, expected_output)

    def test_search_expert_knowledge_no_documents_field_at_all(self):
        query = "query for no docs field"
        mock_response = {
            "documents": None, # Documents field is None
        }
        self.mock_expert_collection.query.return_value = mock_response
        
        expected_output = ""
        result = self.system.search_expert_knowledge(query)
        self.assertEqual(result, expected_output)

    def test_search_expert_knowledge_fewer_than_n_results(self):
        query = "less results query"
        mock_response = {
            "documents": [["doc1 text", "doc2 text"]],
            "ids": [["id1", "id2"]],
        }
        self.mock_expert_collection.query.return_value = mock_response
        
        expected_joined_docs = "doc1 text\n\ndoc2 text"
        result = self.system.search_expert_knowledge(query, n_results=5) # Asking for 5, getting 2
        
        self.assertEqual(result, expected_joined_docs)

    # --- Tests for evaluate_response_depth ---
    def test_evaluate_response_depth_valid_score3_and_rationale(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "Score: 3\nRationale: This is a profound answer."
        self.mock_ollama_client.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 3)
        self.assertEqual(rationale, "This is a profound answer.")
        self.mock_ollama_client.generate.assert_called_once()

    def test_evaluate_response_depth_valid_score1_and_rationale_case_insensitive(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "score: 1\nrationale: Surface level."
        self.mock_ollama_client.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 1)
        self.assertEqual(rationale, "Surface level.")

    def test_evaluate_response_depth_only_score(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "Score: 2"
        self.mock_ollama_client.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 2)
        self.assertEqual(rationale, "Rationale not clearly articulated by evaluator.")

    def test_evaluate_response_depth_malformed_output(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "This is completely invalid output."
        self.mock_ollama_client.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 2)
        self.assertTrue("Default score due to parsing error." in rationale)
        self.assertTrue(f"Raw output: '{mock_llm_output[:100]}...'" in rationale)


    def test_evaluate_response_depth_just_a_number(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "1" # LLM returns just a number
        self.mock_ollama_client.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 1)
        self.assertEqual(rationale, "No rationale provided (single number response).")

    def test_evaluate_response_depth_score_and_rationale_with_extra_text(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "Okay, I've evaluated. Score: 2\nRationale: It's okay, but not great. Some more details here."
        self.mock_ollama_client.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 2)
        self.assertEqual(rationale, "It's okay, but not great. Some more details here.")

    def test_evaluate_response_depth_exception_during_llm_call(self):
        question = "Test Question"
        response_text = "Test Response"
        self.mock_ollama_client.generate.side_effect = Exception("LLM unavailable")

        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 2) # Default score
        self.assertTrue("Default score due to exception during parsing" in rationale)
        self.assertTrue("LLM unavailable" in rationale) # Check if the exception message is in the rationale

if __name__ == '__main__':
    unittest.main()
