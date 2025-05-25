import unittest
from unittest.mock import patch, MagicMock, call
import io
import sys

# Add the parent directory to sys.path to allow importing interview_system
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from interview_system import RecursiveInterviewSystem

class TestRecursiveInterviewSystem(unittest.TestCase):

    def setUp(self):
        """Set up for each test method."""
        # Mock external clients
        self.mock_ollama_client_instance = MagicMock(spec=sys.modules['ollama'].Client)
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
                'interview_opening': {
                    'host_introduction': "Test welcome to The Recursive",
                    'expert_introduction_template': "Test {expert_name}, you've had {years_evolved} years to evolve, what about {core_theme}?"
                },
                'question_generation': {
                    'opening_question': "Test opening question for {topic} with {expert_name}",
                    'follow_up_question': "Test follow-up based on {expert_response_text}"
                },
                'expert_response': {
                    'main_prompt': "Test {expert_name} age {expert_age} respond to {question} with knowledge {relevant_knowledge}"
                },
                'evaluation': {
                    'main_prompt': "Test evaluate {question} and {response}",
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
            'default_topics': ["Test Topic 1"],
            'expert_defaults': {
                'martin_luther_king_jr': {
                    'expert_age': 96,
                    'years_evolved': 57,
                    'core_theme': "test justice theme"
                }
            }
        }

        # Configure the mock ChromaDB client's get_or_create_collection
        def get_collection_side_effect(name, **kwargs):
            if name == self.system.config['chromadb']['host_collection_name']:
                return self.mock_host_collection
            elif name == self.system.config['chromadb']['expert_collection_name']:
                return self.mock_expert_collection
            return MagicMock()

        self.mock_chromadb_client_instance.get_or_create_collection.side_effect = get_collection_side_effect
        
        # Re-assign system's client and collection attributes to our mocks
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
        expected = ""
        self.assertEqual(self.system.clean_response(text), expected)

    # --- Tests for perform_web_search ---
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_perform_web_search(self, mock_stdout):
        query = "test query for web search"
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
        }
        self.mock_expert_collection.query.return_value = mock_response
        
        expected_joined_docs = "doc1 text\n\ndoc2 text\n\ndoc3 text"
        result = self.system.search_expert_knowledge(query, n_results=3) 
        self.assertEqual(result, expected_joined_docs)
        self.mock_expert_collection.query.assert_called_once_with(query_texts=[query], n_results=3)

        # Test with n_results from config
        self.mock_expert_collection.query.reset_mock()
        self.mock_expert_collection.query.return_value = mock_response
        result_config_n_results = self.system.search_expert_knowledge(query)
        self.assertEqual(result_config_n_results, expected_joined_docs)
        self.mock_expert_collection.query.assert_called_once_with(query_texts=[query], n_results=self.system.config['chromadb']['default_n_results'])

    def test_search_expert_knowledge_no_documents_in_results(self):
        query = "another query"
        mock_response = {
            "documents": [[]],
            "ids": [[]],
        }
        self.mock_expert_collection.query.return_value = mock_response
        
        expected_output = ""
        result = self.system.search_expert_knowledge(query)
        
        self.assertEqual(result, expected_output)

    def test_search_expert_knowledge_no_documents_field_at_all(self):
        query = "query for no docs field"
        mock_response = {
            "documents": None,
        }
        self.mock_expert_collection.query.return_value = mock_response
        
        expected_output = ""
        result = self.system.search_expert_knowledge(query)
        self.assertEqual(result, expected_output)

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
        mock_llm_output = "1"
        self.mock_ollama_client_instance.generate.return_value = {'response': mock_llm_output}
        
        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 1)
        self.assertEqual(rationale, self.system.config['prompts']['evaluation']['rationale_no_rationale_provided'])

    def test_evaluate_response_depth_exception_during_llm_call(self):
        question = "Test Question"
        response_text = "Test Response"
        self.mock_ollama_client_instance.generate.side_effect = Exception("LLM unavailable")

        score, rationale = self.system.evaluate_response_depth(question, response_text)
        
        self.assertEqual(score, 2)
        expected_rationale_prefix = self.system.config['prompts']['evaluation']['rationale_exception_prefix']
        self.assertTrue(rationale.startswith(expected_rationale_prefix))
        self.assertTrue("LLM unavailable" in rationale)

    # --- Test for generate_host_question ---
    def test_generate_host_question_opening(self):
        topic = "AI ethics"
        self.mock_ollama_client_instance.generate.return_value = {'response': 'What are your thoughts on AI ethics?'}
        
        result = self.system.generate_host_question(topic)
        
        self.assertEqual(result, 'What are your thoughts on AI ethics?')
        self.mock_ollama_client_instance.generate.assert_called_once()

    def test_generate_host_question_followup(self):
        topic = "AI ethics"
        conversation_history = "Previous conversation..."
        expert_response = "I think AI should be regulated."
        self.mock_ollama_client_instance.generate.return_value = {'response': 'But how would you implement that regulation?'}
        
        result = self.system.generate_host_question(topic, conversation_history, is_followup=True, expert_response_text=expert_response)
        
        self.assertEqual(result, 'But how would you implement that regulation?')
        self.mock_ollama_client_instance.generate.assert_called_once()

    # --- Test for setup_mlk_expert ---
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_setup_mlk_expert_success(self, mock_open):
        mock_persona_content = """
# Martin Luther King Jr. — Evolved Digital Persona (1929-2025)

**MLK:** I am Martin Luther King Jr., now 96 years old in 2025.
This is a valid chunk.

HOST: This should be skipped.
**MLK:** Another valid chunk, short but over 20 chars.

## A Markdown Heading
---
A separator
Short line.
**MLK:** This line is long enough to be included.
"""
        mock_open.read_data = mock_persona_content
        mock_open.return_value.read.return_value = mock_persona_content
        
        self.system.config['persona_settings']['default_persona_file_path'] = "personas/dummy_mlk.md"
        
        self.system.setup_mlk_expert()

        self.mock_expert_collection.upsert.assert_called_once()
        args, _ = self.mock_expert_collection.upsert.call_args
        
        expected_docs = [
            "I am Martin Luther King Jr., now 96 years old in 2025.\nThis is a valid chunk.",
            "Another valid chunk, short but over 20 chars.",
            "This line is long enough to be included."
        ]
        self.assertEqual(args[0]['documents'], expected_docs)
        
        expected_ids = [
            self.system.config['persona_settings']['persona_doc_id_prefix'] + "1",
            self.system.config['persona_settings']['persona_doc_id_prefix'] + "2",
            self.system.config['persona_settings']['persona_doc_id_prefix'] + "3",
        ]
        self.assertEqual(args[0]['ids'], expected_ids)
        
        expected_metadatas = [
            {"source": "personas/dummy_mlk.md", "type": "base_persona"},
            {"source": "personas/dummy_mlk.md", "type": "base_persona"},
            {"source": "personas/dummy_mlk.md", "type": "base_persona"},
        ]
        self.assertEqual(args[0]['metadatas'], expected_metadatas)

    @patch('builtins.open', side_effect=FileNotFoundError("File not found for testing"))
    @patch('sys.stdout', new_callable=io.StringIO) # To capture print statements
    def test_setup_mlk_expert_file_not_found_uses_fallback(self, mock_stdout, mock_open):
        self.system.config['persona_settings']['default_persona_file_path'] = "personas/non_existent.md"
        
        self.system.setup_mlk_expert()
        
        self.assertIn("Error reading persona file personas/non_existent.md: File not found for testing. Using fallback knowledge.", mock_stdout.getvalue())
        
        self.mock_expert_collection.upsert.assert_called_once()
        args, _ = self.mock_expert_collection.upsert.call_args
        
        # Check if fallback documents are being processed
        self.assertTrue(len(args[0]['documents']) > 0)
        self.assertTrue("I am Martin Luther King Jr., now 96 years old in 2025." in args[0]['documents'][0])
        self.assertEqual(args[0]['metadatas'][0]['source'], "personas/non_existent.md") # Source still reflects attempted path

    # --- Tests for detect_comfort_zone_patterns ---
    def test_detect_comfort_zone_patterns(self):
        # Setup comfort zone phrases in config for this test
        self.system.config['expert_defaults']['martin_luther_king_jr']['comfort_zone_phrases'] = [
            "the arc of the moral universe",
            "beloved community",
            "nonviolence is the answer"
        ]
        self.system.comfort_zone_patterns = [] # Reset for each test scenario if needed

        # Case 1: Single phrase found
        response1 = "We must strive for the beloved community."
        is_comfort, patterns = self.system.detect_comfort_zone_patterns(response1, "MLK")
        self.assertTrue(is_comfort)
        self.assertEqual(patterns, ["beloved community"])
        self.assertEqual(self.system.comfort_zone_patterns, ["beloved community"])

        # Case 2: Multiple phrases found (and case insensitivity)
        self.system.comfort_zone_patterns = [] # Reset
        response2 = "The Arc of the Moral Universe is long, but it bends towards justice. Nonviolence is the answer."
        is_comfort, patterns = self.system.detect_comfort_zone_patterns(response2, "MLK")
        self.assertTrue(is_comfort)
        self.assertIn("the arc of the moral universe", patterns)
        self.assertIn("nonviolence is the answer", patterns)
        self.assertIn("the arc of the moral universe", self.system.comfort_zone_patterns)
        self.assertIn("nonviolence is the answer", self.system.comfort_zone_patterns)

        # Case 3: No comfort phrase found
        self.system.comfort_zone_patterns = [] # Reset
        response3 = "This is a new thought about digital ethics."
        is_comfort, patterns = self.system.detect_comfort_zone_patterns(response3, "MLK")
        self.assertFalse(is_comfort)
        self.assertEqual(patterns, [])
        self.assertEqual(self.system.comfort_zone_patterns, [])

        # Case 4: Empty response
        self.system.comfort_zone_patterns = [] # Reset
        response4 = ""
        is_comfort, patterns = self.system.detect_comfort_zone_patterns(response4, "MLK")
        self.assertFalse(is_comfort)
        self.assertEqual(patterns, [])
        self.assertEqual(self.system.comfort_zone_patterns, [])

    # --- Test for generate_expert_response ---
    def test_generate_expert_response(self):
        expert_name = "Test Expert"
        question = "What do you think about AI?"
        conversation_history = "Previous context..."
        
        # Mock the knowledge search
        self.mock_expert_collection.query.return_value = {
            "documents": [["Some relevant knowledge about AI"]],
            "ids": [["doc1"]]
        }
        # Mock web search (as it's part of generate_expert_response now)
        with patch.object(self.system, 'perform_web_search', return_value=[]) as mock_web_search:
            self.mock_ollama_client_instance.generate.return_value = {'response': 'AI is a powerful tool that requires careful consideration.'}
            
            result = self.system.generate_expert_response(expert_name, question, conversation_history)
            
            self.assertEqual(result, 'AI is a powerful tool that requires careful consideration.')
            self.mock_ollama_client_instance.generate.assert_called_once()
            mock_web_search.assert_called_once_with(question)


    # --- Basic End-to-End Test for run_interview ---
    @patch.object(RecursiveInterviewSystem, 'save_transcript')
    @patch.object(RecursiveInterviewSystem, 'setup_mlk_expert')
    @patch.object(RecursiveInterviewSystem, 'perform_web_search', return_value=[]) # Mock web search to return no snippets
    @patch.object(RecursiveInterviewSystem, 'detect_comfort_zone_patterns', return_value=(False, [])) # Mock comfort zone
    def test_run_interview_basic_flow(self, mock_detect_comfort, mock_perform_web_search, mock_setup_expert, mock_save_transcript):
        # Define the sequence of responses from the LLM
        self.mock_ollama_client_instance.generate.side_effect = [
            # 1. Host Introduction (conduct_interview_opening calls generate_expert_response)
            {'response': "I'm Test Expert, evolved and ready."},  # Expert's intro response
            # 2. Host asks opening question for Topic 1
            {'response': "What is your opening thought on Test Topic 1?"}, # Host's opening question
            # 3. Expert responds to opening question
            {'response': "My opening thought on Test Topic 1 is positive."}, # Expert's response
            # 4. Evaluation of expert's response (let's say it's depth 2, needs follow-up)
            {'response': "Score: 2\nRationale: A bit shallow, needs more."},
            # 5. Host asks follow-up question
            {'response': "Can you elaborate further on Test Topic 1?"}, # Host's follow-up
            # 6. Expert responds to follow-up
            {'response': "Elaborating further, Test Topic 1 is complex but promising."}, # Expert's follow-up response
            # 7. Evaluation of follow-up (let's say it's depth 3, good)
            {'response': "Score: 3\nRationale: Excellent depth achieved."},
            # 8. Conclusion
            {'response': "This was a great interview. We covered Test Topic 1 well. The end."} # Host's conclusion
        ]

        # Mock RAG queries to return empty
        self.mock_expert_collection.query.return_value = {"documents": [[]], "ids": [[]]}
        self.mock_host_collection.query.return_value = {"documents": [[]], "ids": [[]]}

        # Run the interview
        self.system.run_interview(
            expert_name="Test Expert", 
            topics=["Test Topic 1"], 
            max_exchanges=self.system.config['interview']['max_exchanges'] # Use configured max_exchanges
        )

        # Assertions
        mock_setup_expert.assert_called_once() # From main() call if not mocked there, or here if part of run_interview setup
        
        # Check that generate was called multiple times (exact number can be tricky due to complex flow)
        self.assertTrue(self.mock_ollama_client_instance.generate.call_count >= 7) # Intro, Q1, R1, E1, FUpQ1, FUpR1, E2, Conclusion

        # Check some key calls to generate (using call_args_list to inspect specific calls)
        # This is illustrative; specific prompts depend heavily on your templates
        # For example, check if the evaluation prompt was called
        evaluation_prompt_template = self.system.config['prompts']['evaluation']['main_prompt']
        made_evaluation_call = any(
            evaluation_prompt_template.split(" ")[0] in call_args[0][0].get('prompt', '')
            for call_args in self.mock_ollama_client_instance.generate.call_args_list
        )
        self.assertTrue(made_evaluation_call, "Evaluation prompt was not generated.")

        # Check if the conclusion prompt was called
        # This is a simplified check; you might need to be more specific
        made_conclusion_call = any(
            "concluded an interview with Test Expert" in call_args[0][0].get('prompt', '')
            for call_args in self.mock_ollama_client_instance.generate.call_args_list
        )
        self.assertTrue(made_conclusion_call, "Conclusion prompt was not generated.")

        mock_save_transcript.assert_called_once()
        mock_perform_web_search.assert_called() # Called during expert responses
        mock_detect_comfort.assert_called() # Called after expert responses

if __name__ == '__main__':
    unittest.main()