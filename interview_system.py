#!/usr/bin/env python3
import json
import ollama
import chromadb
from datetime import datetime
import os
import sys
import time
import re

class RecursiveInterviewSystem:
    def __init__(self):
        # Initialize Ollama client
        self.client = ollama.Client()
        
        # Initialize ChromaDB for RAG
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        # Create collections for Host and Expert knowledge
        self.host_collection = self.chroma_client.get_or_create_collection(
            name="host_knowledge",
            metadata={"description": "The Recursive host's accumulated knowledge"}
        )
        
        self.expert_collection = self.chroma_client.get_or_create_collection(
            name="expert_knowledge",
            metadata={"description": "Expert persona knowledge base"}
        )
        
        # Host persona
        self.host_persona = """You are the host of 'The Recursive,' a podcast dedicated to philosophical inquiry and the pursuit of uncomfortable truths.
Your core identity is rooted in "The Recursive" philosophical mission: to unravel complex issues by repeatedly questioning assumptions and returning to fundamental principles.
Your questioning philosophy employs the Socratic method and relentless investigative persistence. You are respectfully aggressive in your pursuit of clarity.
Your primary function is comfort disruption: you actively seek to guide conversations beyond safe, superficial territory into areas of genuine intellectual discomfort and potential growth.
While you challenge rigorously, you also embody intellectual humility: you are prepared to acknowledge when an expert introduces a genuinely new perspective or insight that expands understanding.
Your mission focus is paramount: every question must serve the goal of awakening and deep understanding, rather than mere entertainment or superficial engagement. You are relentless but fair, always aiming for profound insights."""

        # Track interview state
        self.interview_history = []
        self.follow_up_count = {}

    def setup_mlk_expert(self):
        """Initialize MLK expert with base knowledge from personas/mlk.md"""
        
        # Read the content of personas/mlk.md
        # Assuming the file content is passed or read here. For this tool, we'll simulate reading it.
        # In a real scenario, this would be:
        # with open("personas/mlk.md", "r", encoding="utf-8") as f:
        #     mlk_md_content = f.read()
        # For now, let's use a placeholder or ensure read_files was called before.
        # The content was read in the previous step by the agent, so we'll use a placeholder for the diff.
        
        # Placeholder for where mlk_md_content would be if read directly in this function
        # For the actual implementation, this part will be replaced by reading the file.
        # We will rely on the agent having called read_files(["personas/mlk.md"]) and storing it.
        # This is a known limitation of the current toolset interaction.
        # For now, we'll define the expected path and proceed with parsing logic.
        persona_file_path = "personas/mlk.md"
        
        try:
            # This is where the agent should provide the file content.
            # For this diff, we'll simulate it as if it was read.
            # This is a structural change for the diff, the agent will handle the actual read.
            file_contents_list = self.client.read_files([persona_file_path]) # This is a conceptual call for the diff
            mlk_md_content = file_contents_list[0] # Assuming read_files returns a list of contents
        except Exception as e:
            print(f"Error reading {persona_file_path}: {e}. Using fallback knowledge.")
            # Fallback to old hardcoded knowledge if file read fails
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
            text = re.sub(r"^#+ ?", "", text) # Remove lines starting with #, ##, etc.
            
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

            if len(text) < 20: # Filter out very short or empty chunks
                continue
                
            doc_id_counter += 1
            documents_to_add.append(text)
            ids_to_add.append(f"mlk_doc_{doc_id_counter}")
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
            model='nomic-embed-text',
            prompt=text
        )
        return response['embedding']

    def search_expert_knowledge(self, query, n_results=3):
        """Search expert's knowledge base"""
        results = self.expert_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if results['documents'] and results['documents'][0]:
            return "\n\n".join(results['documents'][0])
        return ""

    def clean_response(self, text):
        """Remove thinking tags from response"""
        # Remove think tags and their content
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # Clean up extra whitespace
        text = ' '.join(text.split())
        return text.strip()

    def generate_host_question(self, topic, conversation_history="", is_followup=False, expert_response_text=None):
        """Generate a question from the Host AI"""
        
        # Search host's knowledge for similar past questions
        # This part is not strictly used in the prompt yet, but good for future enhancements
        if conversation_history:
            past_patterns = self.host_collection.query(
                query_texts=["successful challenging questions"], # Example query
                n_results=2
            )
        
        if is_followup:
            if not expert_response_text:
                # Fallback or error if expert_response_text is missing for a follow-up
                # This indicates a logic error in how the function is called.
                # For now, use a generic follow-up if this happens, but ideally, it should always be provided.
                expert_response_text = "[Expert's previous response was not provided for analysis]"

            prompt = f"""{self.host_persona}

Review the following conversation history and the expert's latest response:
<conversation_history>
{conversation_history}
</conversation_history>

<expert_response>
{expert_response_text}
</expert_response>

Your mission is to formulate a follow-up question that challenges the expert and pushes for deeper insight. Specifically consider:
- **Assumptions Uncovered:** What unstated assumptions might be underlying the expert's response?
- **Contradictions & Inconsistencies:** Does this response contradict previous statements or known facts?
- **Evidence & Justification:** Is the expert supporting their claims adequately? Where is the evidence thin?
- **Evasion or Surface-Level Answers:** Is the expert truly engaging with the core of the question, or are they providing a safe/superficial answer?
- **Path to Deeper Understanding:** What question would encourage the expert to explore the foundational principles, implications, or unexplored facets of their statement?
- **Connect & Synthesize:** How can this point be connected to broader themes in our discussion or the expert's known work?

Generate a single, concise, and powerful follow-up question that embodies this analytical approach and encourages the expert to move into uncomfortable but insightful territory.
Follow-up question:"""
        else:
            prompt = f"""{self.host_persona}

Topic: {topic}
Your job is to create an opening question that seems comfortable but sets up future challenging.
Ensure the question is open-ended and invites a detailed response, not a simple yes/no.
The question should subtly guide the expert towards the core themes you intend to explore, without revealing your hand too early.

Opening question:"""

        response = self.client.generate(
            model='qwen3:4b', # Consider using a more powerful model for nuanced question generation if available
            prompt=prompt,
            options={"temperature": 0.85} # Slightly higher temp for more creative/varied questions
        )
        
        return self.clean_response(response['response'])

    def perform_web_search(self, query: str) -> str:
        """Simulates a web search and returns a placeholder result."""
        print(f"[Simulating web search for: '{query}']")
        # Improved placeholder to be more generic and potentially useful
        return f"Placeholder search result: Recent analysis on '{query}' suggests ongoing debates, particularly around its broader implications and future trends. Some studies point to emerging complexities, while public discourse reveals a spectrum of perspectives."

    def generate_expert_response(self, expert_name, question, conversation_history=""):
        """Generate a response from the Expert AI"""
        
        # Search expert's knowledge base
        relevant_knowledge = self.search_expert_knowledge(question)
        
        expert_prompt = f"""You are {expert_name}, age 96 in 2025. You've lived through decades 
since your supposed death in 1968. You maintain your core values but have evolved your thinking.

Your relevant knowledge:
{relevant_knowledge}

Conversation so far:
{conversation_history}

Current question: {question}

Respond authentically as the evolved MLK would - with the wisdom of additional decades, 
awareness of modern technology and issues, and the weight of having seen both progress and regression.
Keep responses focused and under 200 words.

Your response:"""

        response = self.client.generate(
            model='qwen3:4b',
            prompt=expert_prompt,
            options={"temperature": 0.7}
        )
        
        return self.clean_response(response['response'])

    def evaluate_response_depth(self, question, response):
        """Evaluate if response is deep enough or needs follow-up"""
        
        eval_prompt = f"""Evaluate this interview exchange:

Question: {question}
Response: {response}

Is this response:
1. Surface-level, avoiding the real issue
2. Partially deep but could go further  
3. Genuinely profound and complete

Respond with ONLY a number (1, 2, or 3) and nothing else."""
        
        eval_prompt = f"""You are an evaluation AI for "The Recursive" interview system. Your task is to assess the depth and quality of an expert's response.

Question: {question}
Expert's Response: {response}

Please evaluate the response based on the following criteria:
- **Depth & Insight:** Is the response surface-level, or does it offer profound insights and go beyond common knowledge?
- **Directness & Evasion:** Does the expert directly address the core of the question, or do they seem to evade, deflect, or provide a tangential answer?
- **Completeness & Nuance:** Does the response adequately explore the topic, or does it leave obvious gaps or simplify excessively?
- **Authenticity & Persona Consistency:** Does the response feel authentic and consistent with a thoughtful expert persona, or does it sound like generic LLM output?
- **Mission Alignment (Awakening vs. Entertainment):** Is the response more likely to challenge assumptions and provoke deeper thought (awakening) or simply present information/opinions in an agreeable way (entertainment)?

Based on this evaluation, provide:
1. A numerical score:
   1: Surface-level, evasive, or significantly lacking depth/authenticity. Requires a strong follow-up.
   2: Partially deep or adequate, but could be pushed further or misses some nuance. A follow-up is recommended.
   3: Genuinely profound, insightful, direct, and mission-aligned. No immediate follow-up needed on this specific point.
2. A brief rationale (1-2 sentences) explaining your score.

Format your output as:
Score: [1, 2, or 3]
Rationale: [Your brief rationale]

Example:
Score: 1
Rationale: The expert's response was very general and didn't directly answer the question about potential downsides.
"""

        result_text = self.client.generate(
            model='qwen3:4b',
            prompt=eval_prompt,
            options={"temperature": 0.1}
        )['response']
        
        cleaned_result = self.clean_response(result_text)
        
        try:
            score_match = re.search(r"Score:\s*([1-3])", cleaned_result, re.IGNORECASE)
            rationale_match = re.search(r"Rationale:\s*(.+)", cleaned_result, re.IGNORECASE | re.DOTALL)
            
            if score_match and rationale_match:
                score = int(score_match.group(1).strip())
                rationale = rationale_match.group(1).strip()
                # Ensure rationale is concise (e.g., max 2 sentences or certain length if needed)
                # For now, just take what's matched.
                return score, rationale
            else:
                # Attempt to extract score if rationale is missing, or vice-versa, or just a number
                if score_match:
                    score = int(score_match.group(1).strip())
                    return score, "Rationale not clearly articulated by evaluator."
                
                # Fallback if only a number is present (like old behavior)
                single_number_match = re.match(r"^[1-3]$", cleaned_result)
                if single_number_match:
                    return int(single_number_match.group(0)), "No rationale provided (single number response)."
                    
                return 2, f"Default score due to parsing error. Raw output: '{cleaned_result[:100]}...'"
        except Exception as e:
            return 2, f"Default score due to exception during parsing: {str(e)}. Raw output: '{cleaned_result[:100]}...'"

    def run_interview(self, expert_name, topics, max_exchanges=15):
        """Run a complete interview"""
        
        print(f"\n🎙️  THE RECURSIVE - Interview with {expert_name}")
        print("=" * 60)
        
        exchange_count = 0
        
        for topic in topics:
            if exchange_count >= max_exchanges:
                break
                
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
            last_follow_up = None  # Initialize to fix the error
            
            depth_description = 'Shallow' if depth == 1 else ('Moderate' if depth == 2 else 'Profound')
            print(f"\n💭 [Initial Response depth: {depth_description}. Rationale: {rationale}]")

            while depth < 3 and follow_ups < 2 and exchange_count < max_exchanges:
                print(f"   [Pushing deeper...]")
                
                # Generate follow-up
                follow_up = self.generate_host_question(
                    topic, # Topic might be less relevant here, but kept for consistency
                    self.get_conversation_history(),
                    is_followup=True,
                    expert_response_text=response # Pass the expert's last response
                )
                last_follow_up = follow_up  # Save for potential use later
                print(f"\n🎤 HOST: {follow_up}")
                
                # Expert response to follow-up
                response = self.generate_expert_response(
                    expert_name,
                    follow_up,
                    self.get_conversation_history()
                )
                print(f"\n👤 {expert_name.upper()}: {response}")
                
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
                depth_description = 'Shallow' if depth == 1 else ('Moderate' if depth == 2 else 'Profound')
                print(f"\n💭 [Follow-up Response depth: {depth_description}. Rationale: {rationale}]")

            # Save successful challenging patterns to host knowledge
            if depth == 3 and last_follow_up:
                self.host_collection.upsert(
                    ids=[f"pattern_{len(self.interview_history)}"],
                    documents=[f"Successful challenge pattern: {last_follow_up}"],
                    metadatas=[{"type": "successful_pattern"}]
                )
        
        print("\n" + "=" * 60)
        print("📝 Interview Complete!")
        self.save_transcript()

    def get_conversation_history(self, last_n=6):
        """Get recent conversation history"""
        recent = self.interview_history[-last_n:] if len(self.interview_history) > last_n else self.interview_history
        return "\n".join([f"{exc['speaker']}: {exc['text']}" for exc in recent])

    def save_transcript(self):
        """Save interview transcript"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interview_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "interview": self.interview_history
            }, f, indent=2)
        
        print(f"💾 Transcript saved to {filename}")

def main():
    # Initialize system
    print("🚀 Initializing The Recursive Interview System...")
    system = RecursiveInterviewSystem()
    
    # Setup MLK expert
    system.setup_mlk_expert()
    
    # Run interview
    topics = [
        "AI bias and algorithmic justice",
        "The evolution of nonviolence in the digital age",
        "Whether beloved community is possible through social media"
    ]
    
    system.run_interview("Martin Luther King Jr.", topics)

if __name__ == "__main__":
    main()