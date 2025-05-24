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
        # Mock external clients
        self.mock_ollama_client_instance = MagicMock(spec=sys.modules['ollama'].Client) # Use sys.modules for spec if ollama is complex
        self.mock_chromadb_client_instance = MagicMock(spec=sys.modules['chromadb'].PersistentClient)

        # Mock collections
        self.mock_host_collection = MagicMock(spec=sys.modules['chromadb'].api.models.Collection.Collection)
        self.mock_expert_collection = MagicMock(spec=sys.modules['chromadb'].api.models.Collection.Collection)
        
        # Patch the client instantiations within RecursiveInterviewSystem's __init__
        self.ollama_patcher = patch('ollama.Client', return_value=self.mock_ollama_client_instance)
        self.chromadb_patcher = patch('chromadb.PersistentClient', return_value=self.mock_chromadb_client_instance)
        
        self.mock_ollama_client = self.ollama_patcher.start()
        self.mock_chromadb_client = self.chromadb_patcher.start()

        # Mock _load_config to prevent file access and return an empty dict initially
        with patch.object(RecursiveInterviewSystem, '_load_config', return_value={}) as mock_load_config:
            self.system = RecursiveInterviewSystem()
            # mock_load_config.assert_called_once() # Optional

        # Override self.system.config with a comprehensive mock config for tests
        self.system.config = {
            'chromadb': {
                'path': "./test_db",
                'host_collection_name': "test_host_knowledge",
                'expert_collection_name': "test_expert_knowledge",
                'default_n_results': 3,
                'host_pattern_n_results': 2
            },
            'host_ai_settings': {
                'host_persona_definition': "Test Host Persona",
                'host_knowledge': {
                    'successful_pattern_query': "test successful questions",
                    'pattern_id_prefix': "test_pattern_",
                    'pattern_metadata_type': "test_successful_pattern"
                }
            },
            'persona_settings': {
                'default_persona_file_path': "personas/test_persona.md",
                'persona_doc_id_prefix': "test_doc_"
            },
            'embedding_model': 'test-embed-model',
            'host_llm_model': 'test-host-llm',
            'host_llm_temperature': 0.75,
            'expert_llm_model': 'test-expert-llm',
            'expert_llm_temperature': 0.6,
            'expert_response_max_words': 50,
            'evaluation_llm_model': 'test-eval-llm',
            'evaluation_llm_temperature': 0.05,
            'prompts': {
                'web_search_placeholder': "Test web search placeholder: {query}",
                'evaluation': {
                    'rationale_not_articulated': "Test: Rationale not articulated.",
                    'rationale_no_rationale_provided': "Test: No rationale.",
                    'rationale_parsing_error_prefix': "Test: Parse error prefix.",
                    'rationale_exception_prefix': "Test: Exception prefix."
                }
            },
            'interview': {
                'max_exchanges': 5,
                'max_follow_ups_per_response': 1,
                'conversation_history_last_n': 3
            },
            'transcript_filename_prefix': "test_interview_",
            'transcript_filename_suffix': ".test.json",
            'default_expert_name': "Test Expert",
            'default_topics': ["Test Topic 1"]
        }

        # Configure the mock ChromaDB client's get_or_create_collection
        # to return the correct mock collection based on the (now configured) name
        def get_collection_side_effect(name, **kwargs):
            if name == self.system.config['chromadb']['host_collection_name']:
                return self.mock_host_collection
            elif name == self.system.config['chromadb']['expert_collection_name']:
                return self.mock_expert_collection
            return MagicMock() # Default mock if name doesn't match

        self.mock_chromadb_client_instance.get_or_create_collection.side_effect = get_collection_side_effect
        
        # Re-assign system's client and collection attributes to our mocks,
        # as __init__ would have used the config values now
        self.system.client = self.mock_ollama_client_instance
        self.system.chroma_client = self.mock_chromadb_client_instance
        self.system.host_collection = self.mock_host_collection
        self.system.expert_collection = self.mock_expert_collection
        
    def tearDown(self):
        """Clean up after each test."""
        self.ollama_patcher.stop()
        self.chromadb_patcher.stop()

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
        # Use the configured placeholder string
        expected_output = self.system.config['prompts']['web_search_placeholder'].format(query=query)
        
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
        # Test with explicit n_results
        result = self.system.search_expert_knowledge(query, n_results=3) 
        self.assertEqual(result, expected_joined_docs)
        self.mock_expert_collection.query.assert_called_once_with(query_texts=[query], n_results=3)

        # Test with n_results from config (mock_expert_collection.query needs reset)
        self.mock_expert_collection.query.reset_mock()
        self.mock_expert_collection.query.return_value = mock_response
        result_config_n_results = self.system.search_expert_knowledge(query)
        self.assertEqual(result_config_n_results, expected_joined_docs)
        self.mock_expert_collection.query.assert_called_once_with(query_texts=[query], n_results=self.system.config['chromadb']['default_n_results'])


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
        self.mock_ollama_client_instance.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 3)
        self.assertEqual(rationale, "This is a profound answer.")
        self.mock_ollama_client_instance.generate.assert_called_once()

    def test_evaluate_response_depth_valid_score1_and_rationale_case_insensitive(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "score: 1\nrationale: Surface level."
        self.mock_ollama_client_instance.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 1)
        self.assertEqual(rationale, "Surface level.")

    def test_evaluate_response_depth_only_score(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "Score: 2"
        self.mock_ollama_client_instance.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 2)
        self.assertEqual(rationale, self.system.config['prompts']['evaluation']['rationale_not_articulated'])

    def test_evaluate_response_depth_malformed_output(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "This is completely invalid output."
        self.mock_ollama_client_instance.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 2)
        expected_rationale_prefix = self.system.config['prompts']['evaluation']['rationale_parsing_error_prefix']
        self.assertTrue(rationale.startswith(expected_rationale_prefix))
        self.assertTrue(f"'{mock_llm_output[:100]}...'" in rationale)


    def test_evaluate_response_depth_just_a_number(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "1" # LLM returns just a number
        self.mock_ollama_client_instance.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 1)
        self.assertEqual(rationale, self.system.config['prompts']['evaluation']['rationale_no_rationale_provided'])

    def test_evaluate_response_depth_score_and_rationale_with_extra_text(self):
        question = "Test Question"
        response_text = "Test Response"
        mock_llm_output = "Okay, I've evaluated. Score: 2\nRationale: It's okay, but not great. Some more details here."
        self.mock_ollama_client_instance.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 2)
        self.assertEqual(rationale, "It's okay, but not great. Some more details here.")

    def test_evaluate_response_depth_exception_during_llm_call(self):
        question = "Test Question"
        response_text = "Test Response"
        self.mock_ollama_client_instance.generate.side_effect = Exception("LLM unavailable")

        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 2) # Default score
        expected_rationale_prefix = self.system.config['prompts']['evaluation']['rationale_exception_prefix']
        self.assertTrue(rationale.startswith(expected_rationale_prefix))
        self.assertTrue("LLM unavailable" in rationale) # Check if the exception message is in the rationale

if __name__ == '__main__':
    unittest.main()
