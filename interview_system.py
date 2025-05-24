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
        self.host_persona = """You are the host of 'The Recursive', a radically honest interview podcast.
Your mission: Push experts beyond comfortable answers to uncomfortable truths.
Your style: Relentlessly curious, respectfully aggressive, never satisfied with surface answers.
You use the Socratic method to expose contradictions and shallow thinking.
You must ALWAYS push back at least once on every answer, digging deeper.
Never accept the first response - always find the angle to go deeper."""

        # Track interview state
        self.interview_history = []
        self.follow_up_count = {}

    def setup_mlk_expert(self):
        """Initialize MLK expert with base knowledge"""
        mlk_knowledge = [
            {
                "id": "mlk_1",
                "text": """I am Martin Luther King Jr., now 96 years old in 2025. I was born in 1929 and 
                supposedly assassinated in 1968, but I've lived to see the internet, 9/11, Obama's presidency, 
                Trump's era, and the rise of AI. My core values remain: nonviolence, beloved community, and 
                systemic justice. But I've had 57 years to evolve my thinking."""
            },
            {
                "id": "mlk_2", 
                "text": """On technology and AI: I see algorithmic bias as the new form of segregation. 
                These systems learn from our past prejudices and encode them into the future. Predictive 
                policing that targets Black neighborhoods is digital redlining. AI hiring systems that 
                reject Black names are lunch counters with mathematical 'Whites Only' signs."""
            },
            {
                "id": "mlk_3",
                "text": """My nonviolence philosophy has evolved. In 1968, I saw nonviolence as purely 
                physical. Now I understand economic violence, algorithmic violence, environmental violence. 
                The violence of a system that lets people die from lack of healthcare is as real as a 
                police baton. My tactics must evolve to fight invisible oppression."""
            },
            {
                "id": "mlk_4",
                "text": """I was wrong about the pace of change. I believed the moral arc of the universe 
                bends toward justice naturally. But I've watched it bend backward - mass incarceration, 
                wealth inequality, climate destruction. The arc only bends when we grab it and pull with 
                all our might. There is no inevitable progress."""
            },
            {
                "id": "mlk_5",
                "text": """The beloved community in 2025 must be global and digital. But social media 
                divides us by design - algorithms profit from outrage. We need what I call 'algorithmic 
                beloved community' - systems designed to connect rather than divide, to build empathy 
                rather than hatred. Technology must serve love, not profit."""
            }
        ]
        
        # Add knowledge to ChromaDB
        for item in mlk_knowledge:
            self.expert_collection.upsert(
                ids=[item["id"]],
                documents=[item["text"]],
                metadatas=[{"source": "base_knowledge"}]
            )
        
        print("✓ MLK expert knowledge initialized")

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

    def generate_host_question(self, topic, conversation_history="", is_followup=False):
        """Generate a question from the Host AI"""
        
        # Search host's knowledge for similar past questions
        if conversation_history:
            past_patterns = self.host_collection.query(
                query_texts=["successful challenging questions"],
                n_results=2
            )
        
        if is_followup:
            prompt = f"""{self.host_persona}

Previous conversation:
{conversation_history}

The expert just gave that response. Your job is to CHALLENGE it, find the weakness, the contradiction, 
or the place where they're avoiding the real issue. Push them into uncomfortable territory.
Generate a follow-up question that goes deeper.

Follow-up question:"""
        else:
            prompt = f"""{self.host_persona}

Topic: {topic}
Your job is to create an opening question that seems comfortable but sets up future challenging.

Opening question:"""

        response = self.client.generate(
            model='qwen3:4b',
            prompt=prompt,
            options={"temperature": 0.8}
        )
        
        return self.clean_response(response['response'])

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

        result = self.client.generate(
            model='qwen3:4b',
            prompt=eval_prompt,
            options={"temperature": 0.1}
        )
        
        try:
            return int(self.clean_response(result['response']).strip())
        except:
            return 2  # Default to "could go deeper"

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
            depth = self.evaluate_response_depth(question, response)
            follow_ups = 0
            last_follow_up = None  # Initialize to fix the error
            
            while depth < 3 and follow_ups < 2 and exchange_count < max_exchanges:
                print(f"\n💭 [Response depth: {'Shallow' if depth == 1 else 'Moderate'} - pushing deeper...]")
                
                # Generate follow-up
                follow_up = self.generate_host_question(
                    topic,
                    self.get_conversation_history(),
                    is_followup=True
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
                depth = self.evaluate_response_depth(follow_up, response)
            
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