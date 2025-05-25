#!/usr/bin/env python3
#
# The Recursive Interview System
# ==============================
# This script implements an AI-powered interview system.
# Its behavior can be configured via the 'config.yaml' file,
# which should be located in the same directory as this script.
#
# To customize settings like LLM models, API keys (if any were used),
# database paths, interview parameters, and persona details,
# please modify the 'config.yaml' file.
#

import json
import ollama
import chromadb
from datetime import datetime
import os
import sys
import time
import re
import yaml
import logging

class RecursiveInterviewSystem:
    def __init__(self):
        self.config = self._load_config()
        
        # Setup logging first
        self._setup_logging()
        
        # Initialize Ollama client
        self.client = ollama.Client()
        
        # Initialize ChromaDB for RAG
        self.chroma_client = chromadb.PersistentClient(
            path=self.config.get('chromadb', {}).get('path', "./chroma_db")
        )
        
        # Create collections for Host and Expert knowledge
        self.host_collection = self.chroma_client.get_or_create_collection(
            name=self.config.get('chromadb', {}).get('host_collection_name', "host_knowledge"),
            metadata={"description": "The Recursive host's accumulated knowledge"}
        )
        
        self.expert_collection = self.chroma_client.get_or_create_collection(
            name=self.config.get('chromadb', {}).get('expert_collection_name', "expert_knowledge"),
            metadata={"description": "Expert persona knowledge base"}
        )
        
        # Host persona from config
        self.host_persona = self.config.get('host_ai_settings', {}).get('host_persona_definition', 
            "You are the host of 'The Recursive,' dedicated to philosophical inquiry and uncomfortable truths.")

        # Track interview state
        self.interview_history = []
        self.follow_up_count = {}
        self.topic_depth_scores = {}  # Track depth achieved per topic
        self.comfort_zone_patterns = []  # Track repeated comfort zone responses

    def _setup_logging(self):
        """Setup comprehensive logging system"""
        logging_config = self.config.get('logging', {})
        
        if not logging_config.get('enabled', True):
            # Create a null logger if logging is disabled
            self.logger = logging.getLogger('recursive_null')
            self.logger.addHandler(logging.NullHandler())
            return
            
        # Create logs directory if it doesn't exist
        log_directory = logging_config.get('log_directory', './logs')
        os.makedirs(log_directory, exist_ok=True)
        
        # Setup main logger
        log_level = getattr(logging, logging_config.get('log_level', 'INFO').upper())
        
        # Create logger
        self.logger = logging.getLogger('recursive_interview')
        self.logger.setLevel(log_level)
        
        # Create file handler with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{logging_config.get('log_filename_prefix', 'recursive_')}{timestamp}.log"
        log_filepath = os.path.join(log_directory, log_filename)
        
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        if not self.logger.handlers:  # Avoid duplicate handlers
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
        self.logger.info("Logging system initialized")
        self.logger.info(f"Log file: {log_filepath}")

    def _log_llm_request(self, request_type: str, model: str, prompt: str, options: dict = None):
        """Log LLM request details"""
        if not self.config.get('logging', {}).get('log_all_llm_requests', True):
            return
            
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'LLM_REQUEST',
            'request_type': request_type,
            'model': model,
            'prompt_length': len(prompt),
            'prompt_preview': prompt[:200] + "..." if len(prompt) > 200 else prompt,
            'options': options or {}
        }
        
        self.logger.info(f"LLM_REQUEST - {request_type}: {json.dumps(log_entry, indent=2)}")

    def _log_llm_response(self, request_type: str, response: dict, processing_time: float = None):
        """Log LLM response details"""
        if not self.config.get('logging', {}).get('log_all_llm_responses', True):
            return
            
        response_text = response.get('response', '') if isinstance(response, dict) else str(response)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'LLM_RESPONSE',
            'request_type': request_type,
            'response_length': len(response_text),
            'response_preview': response_text[:200] + "..." if len(response_text) > 200 else response_text,
            'full_response': response_text,  # Full response for debugging
            'processing_time_seconds': processing_time
        }
        
        self.logger.info(f"LLM_RESPONSE - {request_type}: {json.dumps(log_entry, indent=2)}")

    def _make_llm_request(self, request_type: str, model: str, prompt: str, options: dict = None):
        """Make LLM request with logging"""
        start_time = time.time()
        
        # Log the request
        self._log_llm_request(request_type, model, prompt, options)
        
        try:
            # Make the actual request
            response = self.client.generate(
                model=model,
                prompt=prompt,
                options=options or {}
            )
            
            processing_time = time.time() - start_time
            
            # Log the response
            self._log_llm_response(request_type, response, processing_time)
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_response = {'response': f'ERROR: {str(e)}', 'error': True}
            
            self.logger.error(f"LLM request failed for {request_type}: {str(e)}")
            self._log_llm_response(request_type, error_response, processing_time)
            
            raise

    def _load_config(self, config_path="config.yaml") -> dict:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                if config_data is None:
                    print(f"Warning: {config_path} is empty or not valid YAML. Proceeding with an empty configuration.")
                    return {} 
                print(f"✓ Configuration loaded from {config_path}")
                return config_data
        except FileNotFoundError:
            print(f"Error: Configuration file {config_path} not found. Proceeding with an empty configuration.")
            raise
        except yaml.YAMLError as e:
            print(f"Error parsing YAML from {config_path}: {e}. Proceeding with an empty configuration.")
            raise

    def setup_mlk_expert(self):
        """Initialize MLK expert with base knowledge from personas/mlk.md"""
        
        persona_file_path = self.config.get('persona_settings', {}).get('default_persona_file_path', "personas/mlk.md")
        
        try:
            with open(persona_file_path, "r", encoding="utf-8") as f:
                mlk_md_content = f.read()
        except Exception as e:
            print(f"Error reading persona file {persona_file_path}: {e}. Using fallback knowledge.")
            mlk_md_content = """
# Martin Luther King Jr. — Evolved Digital Persona (1929-2025)

**MLK:** I am Martin Luther King Jr., now 96 years old in 2025.
I was born in 1929 and supposedly assassinated in 1968, but I've lived to see the internet, 9/11, Obama's presidency, Trump's era, and the rise of AI.
My core values remain: nonviolence, beloved community, and systemic justice. But I've had 57 years to evolve my thinking.

**MLK:** On technology and AI: I see algorithmic bias as the new form of segregation.
These systems learn from our past prejudices and encode them into the future. Predictive policing that targets Black neighborhoods is digital redlining. AI hiring systems that reject Black names are lunch counters with mathematical 'Whites Only' signs.
"""

        # Split content by double newlines
        raw_chunks = mlk_md_content.split('\n\n')
        
        documents_to_add = []
        ids_to_add = []
        metadatas_to_add = []
        doc_id_counter = 0
        
        for chunk in raw_chunks:
            text = chunk.strip()
            
            # Skip HOST lines
            if text.startswith("**HOST:") or text.startswith("HOST:"):
                continue

            # Remove speaker tags like **MLK:** or MLK:
            text = re.sub(r"^\*\*MLK:\*\* ?", "", text)
            text = re.sub(r"^MLK: ?", "", text)
            
            # Remove Markdown headings
            text = re.sub(r"^#+ ?", "", text)
            
            # Remove lines that are just separators or metadata-like
            if text.startswith("---") or text.startswith("## ") or text.startswith("### "):
                continue
            if text.lower().startswith("featured persona:") or \
               text.lower().startswith("theme:") or \
               text.lower().startswith("background evolution") or \
               text.lower().startswith("core unchanging values") or \
               text.lower().startswith("evolutionary developments") or \
               text.lower().startswith("style evolution") or \
               text.lower().startswith("recursive questioning triggers") or \
               text.lower().startswith("self-correction moments") or \
               text.lower().startswith("modern issues synthesis") or \
               text.lower().startswith("failsafes") or \
               text.lower().startswith("voice synthesis notes"):
                continue

            # Clean up multiple newlines within a chunk that might have been missed
            text = re.sub(r"\n+", "\n", text).strip()

            if len(text) < 20:
                continue
                
            doc_id_counter += 1
            documents_to_add.append(text)
            doc_id_prefix = self.config.get('persona_settings', {}).get('persona_doc_id_prefix', "mlk_doc_")
            ids_to_add.append(f"{doc_id_prefix}{doc_id_counter}")
            metadatas_to_add.append({"source": persona_file_path})

        if documents_to_add:
            self.expert_collection.upsert(
                ids=ids_to_add,
                documents=documents_to_add,
                metadatas=metadatas_to_add
            )
            print(f"✓ MLK expert knowledge initialized from {persona_file_path} with {len(documents_to_add)} documents.")
        else:
            print(f"⚠️ No documents were extracted from {persona_file_path}. MLK expert knowledge might be empty.")

    def get_embedding(self, text):
        """Generate embeddings using Ollama"""
        response = self.client.embeddings(
            model=self.config.get('embedding_model', 'nomic-embed-text'),
            prompt=text
        )
        return response['embedding']

    def search_expert_knowledge(self, query, n_results=None):
        """Search expert's knowledge base"""
        if n_results is None:
            n_results = self.config.get('chromadb', {}).get('default_n_results', 3)
            
        results = self.expert_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if results['documents'] and results['documents'][0]:
            return "\n\n".join(results['documents'][0])
        return ""

    def clean_response(self, text):
        """Remove thinking tags and clean up response formatting"""
        # Remove <think> tags and their content
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # Remove **Label:** formatting like **Opening Question:** or **Follow-up Question:**
        text = re.sub(r'\*\*(Opening|Follow-up) Question:\*\*\s*"?', '', text)
        
        # Remove **Rationale:** and the rest of its line
        text = re.sub(r'\*\*Rationale:\*\*.*', '', text, flags=re.MULTILINE)

        # Remove potential speaker tags like **MLK:** or HOST: at the start
        text = re.sub(r"^\*\*(MLK|HOST):\*\* ?", "", text.strip())
        text = re.sub(r"^(MLK|HOST): ?", "", text.strip())

        # Remove surrounding quotes
        text = text.strip()
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]

        # Clean up extra whitespace and newlines
        text = ' '.join(text.split())
        
        return text.strip()

    def detect_comfort_zone_patterns(self, response, expert_name):
        """Detect if expert is using familiar phrases or comfort zone responses"""
        expert_defaults = self.config.get('expert_defaults', {}).get('martin_luther_king_jr', {})
        comfort_phrases = expert_defaults.get('comfort_zone_phrases', [])
        
        comfort_zone_detected = []
        for phrase in comfort_phrases:
            if phrase.lower() in response.lower():
                comfort_zone_detected.append(phrase)
        
        if comfort_zone_detected:
            self.comfort_zone_patterns.extend(comfort_zone_detected)
            self.logger.info(f"Comfort zone patterns detected: {comfort_zone_detected}")
            
        return len(comfort_zone_detected) > 0, comfort_zone_detected
    
    def conduct_interview_opening(self, expert_name):
        """Conduct the interview opening sequence"""
        self.logger.info(f"Starting interview opening with {expert_name}")
        
        print(f"\n🎙️  THE RECURSIVE")
        print("=" * 60)
        
        # Host introduction
        host_intro = self.config.get('prompts', {}).get('interview_opening', {}).get('host_introduction', 
            "Welcome to The Recursive—where great minds evolve, and comfortable assumptions die.")
        print(f"\n🎤 HOST: {host_intro}")
        
        # Expert introduction question
        expert_defaults = self.config.get('expert_defaults', {}).get('martin_luther_king_jr', {})
        years_evolved = expert_defaults.get('years_evolved', 57)
        core_theme = expert_defaults.get('core_theme', 'justice and social change')
        
        expert_intro_template = self.config.get('prompts', {}).get('interview_opening', {}).get('expert_introduction_template',
            "{expert_name}, thank you for being here. You've had {years_evolved} additional years to evolve your thinking. What would surprise your younger self the most?")
        
        intro_question = expert_intro_template.format(
            expert_name=expert_name,
            years_evolved=years_evolved,
            core_theme=core_theme
        )
        
        print(f"\n🎤 HOST: {intro_question}")
        self.logger.info(f"Opening question posed: {intro_question}")
        
        # Expert opening response
        intro_response = self.generate_expert_response(expert_name, intro_question, "")
        print(f"\n👤 {expert_name.upper()}: {intro_response}")
        
        # Add to history
        self.interview_history.append({
            "speaker": "HOST",
            "text": intro_question,
            "topic": "Introduction"
        })
        self.interview_history.append({
            "speaker": expert_name,
            "text": intro_response,
            "topic": "Introduction"
        })
        
        print(f"\n{'─' * 60}")
        print("🔥 Now let's dig deeper...")
        print("─" * 60)
        self.logger.info("Interview opening completed successfully")

    def generate_host_question(self, topic, conversation_history="", is_followup=False, expert_response_text=None):
        """Generate a question from the Host AI using config prompts"""
        
        # Search host's knowledge for similar past questions
        if conversation_history:
            past_patterns = self.host_collection.query(
                query_texts=[self.config.get('host_ai_settings', {}).get('host_knowledge', {}).get('successful_pattern_query', "successful challenging questions")],
                n_results=self.config.get('chromadb', {}).get('host_pattern_n_results', 2)
            )
        
        if is_followup:
            if not expert_response_text:
                expert_response_text = "[Expert's previous response was not provided for analysis]"

            prompt_template = self.config.get('prompts', {}).get('question_generation', {}).get('follow_up_question', 
                "Generate a challenging follow-up question based on the expert's response.")
            
            prompt = prompt_template.format(
                host_persona=self.host_persona,
                conversation_history=conversation_history,
                expert_response_text=expert_response_text
            )
            request_type = "HOST_FOLLOWUP_QUESTION"
        else:
            prompt_template = self.config.get('prompts', {}).get('question_generation', {}).get('opening_question',
                "Generate an opening question for the topic: {topic}")
            
            prompt = prompt_template.format(
                host_persona=self.host_persona,
                expert_name=self.config.get('default_expert_name', 'Expert'),
                topic=topic
            )
            request_type = "HOST_OPENING_QUESTION"

        response = self._make_llm_request(
            request_type=request_type,
            model=self.config.get('host_llm_model', 'qwen3:4b'),
            prompt=prompt,
            options={"temperature": self.config.get('host_llm_temperature', 0.85)}
        )
        
        cleaned_response = self.clean_response(response['response'])
        self.logger.debug(f"Generated {request_type}: {cleaned_response}")
        
        return cleaned_response

    def perform_web_search(self, query: str) -> str:
        """Simulates a web search and returns a placeholder result."""
        print(f"[Simulating web search for: '{query}']")
        placeholder_template = self.config.get('prompts', {}).get('web_search_placeholder', 
            "Placeholder search result for '{query}'")
        return placeholder_template.format(query=query)

    def generate_expert_response(self, expert_name, question, conversation_history=""):
        """Generate a response from the Expert AI using config prompts"""
        
        # Search expert's knowledge base
        relevant_knowledge = self.search_expert_knowledge(question)
        
        # Get expert defaults
        expert_defaults = self.config.get('expert_defaults', {}).get('martin_luther_king_jr', {})
        expert_age = expert_defaults.get('expert_age', 96)
        max_words = self.config.get('expert_response_max_words', 200)
        
        prompt_template = self.config.get('prompts', {}).get('expert_response', {}).get('main_prompt',
            "You are {expert_name}. Respond to: {question}")
        
        expert_prompt = prompt_template.format(
            expert_name=expert_name,
            expert_age=expert_age,
            relevant_knowledge=relevant_knowledge,
            conversation_history=conversation_history,
            question=question,
            max_words=max_words
        )

        response = self._make_llm_request(
            request_type="EXPERT_RESPONSE",
            model=self.config.get('expert_llm_model', 'qwen3:4b'),
            prompt=expert_prompt,
            options={"temperature": self.config.get('expert_llm_temperature', 0.7)}
        )
        
        cleaned_response = self.clean_response(response['response'])
        self.logger.debug(f"Generated EXPERT_RESPONSE: {cleaned_response}")
        
        return cleaned_response

    def evaluate_response_depth(self, question, response):
        """Evaluate if response is deep enough or needs follow-up using config prompts"""
        
        prompt_template = self.config.get('prompts', {}).get('evaluation', {}).get('main_prompt',
            "Evaluate this response. Score 1-3 and provide rationale.")
        
        eval_prompt = prompt_template.format(
            question=question,
            response=response
        )

        result = self._make_llm_request(
            request_type="RESPONSE_EVALUATION",
            model=self.config.get('evaluation_llm_model', 'qwen3:4b'),
            prompt=eval_prompt,
            options={"temperature": self.config.get('evaluation_llm_temperature', 0.1)}
        )
        
        cleaned_result = self.clean_response(result['response'])
        
        try:
            score_match = re.search(r"Score:\s*([1-3])", cleaned_result, re.IGNORECASE)
            rationale_match = re.search(r"Rationale:\s*(.+)", cleaned_result, re.IGNORECASE | re.DOTALL)
            
            if score_match and rationale_match:
                score = int(score_match.group(1).strip())
                rationale = rationale_match.group(1).strip()
                self.logger.debug(f"Evaluation result: Score {score}, Rationale: {rationale}")
                return score, rationale
            else:
                if score_match:
                    score = int(score_match.group(1).strip())
                    rationale_not_articulated = self.config.get('prompts', {}).get('evaluation', {}).get('rationale_not_articulated', "Rationale not clearly articulated by evaluator.")
                    self.logger.debug(f"Evaluation result: Score {score}, Default rationale used")
                    return score, rationale_not_articulated
                
                # Fallback if only a number is present
                single_number_match = re.match(r"^[1-3]$", cleaned_result)
                if single_number_match:
                    score = int(single_number_match.group(0))
                    rationale_no_rationale = self.config.get('prompts', {}).get('evaluation', {}).get('rationale_no_rationale_provided', "No rationale provided (single number response).")
                    self.logger.debug(f"Evaluation result: Score {score}, Single number response")
                    return score, rationale_no_rationale
                
                # Default case
                rationale_parsing_error_prefix = self.config.get('prompts', {}).get('evaluation', {}).get('rationale_parsing_error_prefix', "Default score due to parsing error. Raw output:")
                self.logger.warning(f"Evaluation parsing failed. Raw output: {cleaned_result}")
                return 2, f"{rationale_parsing_error_prefix} '{cleaned_result[:100]}...'"
        except Exception as e:
            rationale_exception_prefix = self.config.get('prompts', {}).get('evaluation', {}).get('rationale_exception_prefix', "Default score due to exception during parsing:")
            self.logger.error(f"Evaluation exception: {str(e)}. Raw output: {cleaned_result}")
            return 2, f"{rationale_exception_prefix} {str(e)}. Raw output: '{cleaned_result[:100]}...'"

    def generate_interview_conclusion(self, expert_name, topics_covered):
        """Generate a thoughtful conclusion to the interview"""
        
        # Analyze patterns found during interview
        comfort_zone_summary = ""
        if self.comfort_zone_patterns:
            frequent_patterns = {}
            for pattern in self.comfort_zone_patterns:
                frequent_patterns[pattern] = frequent_patterns.get(pattern, 0) + 1
            most_frequent = sorted(frequent_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
            comfort_zone_summary = f"Recurring comfort zone phrases: {[p[0] for p in most_frequent]}"
        
        # Get depth summary
        depth_summary = ""
        if self.topic_depth_scores:
            avg_depth = sum(self.topic_depth_scores.values()) / len(self.topic_depth_scores)
            depth_summary = f"Average depth achieved: {avg_depth:.1f}/3.0"
        
        conclusion_prompt = f"""
        {self.host_persona}

        You have just concluded an interview with {expert_name} covering these topics: {topics_covered}

        Interview Analysis:
        - Total exchanges: {len(self.interview_history)}
        - {comfort_zone_summary if comfort_zone_summary else "No significant comfort zone patterns detected"}
        - {depth_summary if depth_summary else "Depth analysis not available"}

        Generate a thoughtful conclusion that:
        1. Acknowledges what was revealed through the recursive questioning process
        2. Calls out patterns where the expert retreated to familiar territory when pressed
        3. Reflects on what remains unresolved or what deeper questions emerged
        4. Ends with the impact this should have on listeners - were they awakened or entertained?

        This is "The Recursive" - we don't comfort, we challenge. Be honest about whether we succeeded in our mission.

        Generate a concluding statement that synthesizes the interview's journey:
        """
        
        response = self._make_llm_request(
            request_type="INTERVIEW_CONCLUSION",
            model=self.config.get('host_llm_model', 'qwen3:4b'),
            prompt=conclusion_prompt,
            options={"temperature": self.config.get('host_llm_temperature', 0.85)}
        )
        
        return self.clean_response(response['response'])

    def run_interview(self, expert_name, topics, max_exchanges=None):
        """Run a complete interview with proper opening and conclusion"""
        if max_exchanges is None:
            max_exchanges = self.config.get('interview', {}).get('max_exchanges', 15)
        
        self.logger.info(f"Starting interview with {expert_name}, max_exchanges: {max_exchanges}")
        self.logger.info(f"Topics to cover: {topics}")
        
        # Conduct interview opening
        self.conduct_interview_opening(expert_name)
        
        exchange_count = 1  # We've already done the opening exchange
        max_follow_ups = self.config.get('interview', {}).get('max_follow_ups_per_response', 2)
        
        for i, topic in enumerate(topics):
            if exchange_count >= max_exchanges - 2:  # Reserve space for conclusion
                self.logger.warning(f"Near max exchanges ({max_exchanges}), wrapping up after this topic")
                break
                
            self.logger.info(f"Starting topic {i+1}/{len(topics)}: {topic}")
            print(f"\n📋 TOPIC: {topic}")
            print("-" * 40)
            
            # Initial question
            question = self.generate_host_question(topic)
            print(f"\n🎤 HOST: {question}")
            
            # Expert response
            response = self.generate_expert_response(
                expert_name, 
                question,
                self.get_conversation_history()
            )
            print(f"\n👤 {expert_name.upper()}: {response}")
            
            # Check for comfort zone patterns
            is_comfort_zone, comfort_patterns = self.detect_comfort_zone_patterns(response, expert_name)
            if is_comfort_zone:
                print(f"   [🚨 Comfort zone detected: {comfort_patterns[:2]}]")
            
            # Add to history
            self.interview_history.append({
                "speaker": "HOST",
                "text": question,
                "topic": topic
            })
            self.interview_history.append({
                "speaker": expert_name,
                "text": response,
                "topic": topic
            })
            
            exchange_count += 1
            
            # Evaluate and follow up
            depth, rationale = self.evaluate_response_depth(question, response)
            follow_ups = 0
            last_follow_up = None
            best_depth = depth
            
            depth_description = 'Shallow' if depth == 1 else ('Moderate' if depth == 2 else 'Profound')
            print(f"\n💭 [Initial Response depth: {depth_description}. Rationale: {rationale}]")
            self.logger.info(f"Topic '{topic}' initial response depth: {depth} ({depth_description})")

            while depth < 3 and follow_ups < max_follow_ups and exchange_count < max_exchanges - 2:
                self.logger.info(f"Generating follow-up {follow_ups + 1}/{max_follow_ups} for topic '{topic}'")
                print(f"   [Pushing deeper...]")
                
                # Generate follow-up
                follow_up = self.generate_host_question(
                    topic,
                    self.get_conversation_history(),
                    is_followup=True,
                    expert_response_text=response
                )
                last_follow_up = follow_up
                print(f"\n🎤 HOST: {follow_up}")
                
                # Expert response to follow-up
                response = self.generate_expert_response(
                    expert_name,
                    follow_up,
                    self.get_conversation_history()
                )
                print(f"\n👤 {expert_name.upper()}: {response}")
                
                # Check for comfort zone patterns again
                is_comfort_zone, comfort_patterns = self.detect_comfort_zone_patterns(response, expert_name)
                if is_comfort_zone:
                    print(f"   [🚨 Retreating to comfort zone: {comfort_patterns[:2]}]")
                
                # Add to history
                self.interview_history.append({
                    "speaker": "HOST",
                    "text": follow_up,
                    "topic": topic
                })
                self.interview_history.append({
                    "speaker": expert_name,
                    "text": response,
                    "topic": topic
                })
                
                exchange_count += 1
                follow_ups += 1
                
                # Re-evaluate
                depth, rationale = self.evaluate_response_depth(follow_up, response)
                best_depth = max(best_depth, depth)
                depth_description = 'Shallow' if depth == 1 else ('Moderate' if depth == 2 else 'Profound')
                print(f"\n💭 [Follow-up Response depth: {depth_description}. Rationale: {rationale}]")
                self.logger.info(f"Follow-up {follow_ups} depth: {depth} ({depth_description})")

            # Record the best depth achieved for this topic
            self.topic_depth_scores[topic] = best_depth

            # Save successful challenging patterns to host knowledge
            if best_depth == 3 and last_follow_up:
                pattern_id_prefix = self.config.get('host_ai_settings', {}).get('host_knowledge', {}).get('pattern_id_prefix', "pattern_")
                pattern_metadata_type = self.config.get('host_ai_settings', {}).get('host_knowledge', {}).get('pattern_metadata_type', "successful_pattern")
                self.host_collection.upsert(
                    ids=[f"{pattern_id_prefix}{len(self.interview_history)}"],
                    documents=[f"Successful challenge pattern: {last_follow_up}"],
                    metadatas=[{"type": pattern_metadata_type}]
                )
                self.logger.info(f"Saved successful questioning pattern to host knowledge")
            
            self.logger.info(f"Completed topic '{topic}' after {follow_ups} follow-ups, best depth: {best_depth}")
        
        # Generate and deliver conclusion
        print(f"\n{'═' * 60}")
        print("🎯 THE RECURSIVE: Final Analysis")
        print("═" * 60)
        
        conclusion = self.generate_interview_conclusion(expert_name, topics)
        print(f"\n🎤 HOST: {conclusion}")
        
        # Add conclusion to history
        self.interview_history.append({
            "speaker": "HOST",
            "text": conclusion,
            "topic": "Conclusion"
        })
        
        print("\n" + "=" * 60)
        print("📝 Interview Complete! Thank you for joining The Recursive.")
        print("🎯 Remember: If you weren't challenged, we failed. If you were, we succeeded.")
        
        self.logger.info(f"Interview completed. Total exchanges: {len(self.interview_history)}")
        self.logger.info(f"Comfort zone patterns detected: {len(set(self.comfort_zone_patterns))}")
        self.logger.info(f"Topic depth scores: {self.topic_depth_scores}")
        self.save_transcript()

    def get_conversation_history(self, last_n=None):
        """Get recent conversation history"""
        if last_n is None:
            last_n = self.config.get('interview', {}).get('conversation_history_last_n', 6)
        recent = self.interview_history[-last_n:] if len(self.interview_history) > last_n else self.interview_history
        return "\n".join([f"{exc['speaker']}: {exc['text']}" for exc in recent])

    def save_transcript(self):
        """Save interview transcript with logging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = self.config.get('transcript_filename_prefix', "interview_")
        suffix = self.config.get('transcript_filename_suffix', ".json")
        filename = f"{prefix}{timestamp}{suffix}"
        
        transcript_data = {
            "timestamp": timestamp,
            "interview": self.interview_history,
            "metadata": {
                "total_exchanges": len(self.interview_history),
                "expert_name": self.config.get('default_expert_name', 'Unknown'),
                "topics": self.config.get('default_topics', []),
                "topic_depth_scores": self.topic_depth_scores,
                "comfort_zone_patterns_detected": len(set(self.comfort_zone_patterns)),
                "unique_comfort_phrases": list(set(self.comfort_zone_patterns)),
                "config_snapshot": {
                    "host_llm_model": self.config.get('host_llm_model'),
                    "expert_llm_model": self.config.get('expert_llm_model'),
                    "evaluation_llm_model": self.config.get('evaluation_llm_model')
                }
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Transcript saved to {filename}")
        self.logger.info(f"Interview transcript saved to {filename}")
        self.logger.info(f"Final interview statistics: {len(self.interview_history)} total exchanges")

def main():
    # Initialize system
    print("🚀 Initializing The Recursive Interview System...")
    try:
        system = RecursiveInterviewSystem()
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        sys.exit(1)
    
    # Setup MLK expert
    try:
        system.setup_mlk_expert()
    except Exception as e:
        system.logger.error(f"Failed to setup MLK expert: {e}")
        print(f"❌ Failed to setup expert: {e}")
        sys.exit(1)
    
    # Run interview with configurable defaults
    expert_name_to_run = system.config.get('default_expert_name', "Martin Luther King Jr.")
    topics_to_run = system.config.get('default_topics', [
        "AI bias and algorithmic justice",
        "The evolution of nonviolence in the digital age",
        "Whether beloved community is possible through social media"
    ])
    
    system.logger.info(f"Starting interview with {expert_name_to_run}")
    system.logger.info(f"Topics: {topics_to_run}")
    
    try:
        system.run_interview(expert_name_to_run, topics_to_run)
        system.logger.info("Interview completed successfully")
    except Exception as e:
        system.logger.error(f"Interview failed: {e}")
        print(f"❌ Interview failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()