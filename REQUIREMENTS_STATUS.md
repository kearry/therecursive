# The Recursive: Requirements Status

## Purpose

This document translates our vision and workflow into specific, testable requirements for the AI interview system. Every requirement serves the mission: creating authentic conversations that strip away illusions and push toward uncomfortable truths through recursive questioning.

---

## System Architecture Requirements

### **1. Dual AI Configuration**
- [p] **Host AI System**: Must embody "The Recursive" persona with persistent RAG knowledge base
- [p] **Expert AI System**: Must authentically represent specific expert with comprehensive RAG database
- [p] **Real-Time Interaction**: Both AIs must interact dynamically during structured interview process
- [ ] **Independent Learning**: Each AI must evolve and improve from interview experiences
- [p] **Mission Alignment**: All AI behavior must serve awakening rather than entertainment (Guided by persona and prompts)

### **2. RAG Infrastructure Requirements**
- [p] **Dual Database Architecture**: Separate RAG systems for Host and each Expert (Collections exist)
- [ ] **Real-Time Updates**: Both systems must integrate internet research during interviews (Placeholder web search exists, but no RAG update from it)
- [p] **Cross-System Access**: Host AI must access expert knowledge for context and preparation (RAG search on expert collection)
- [p] **Persistent Learning**: All research and insights automatically saved for future reference (Host patterns saved, expert knowledge loaded from files)
- [ ] **Quality Verification**: Automated fact-checking and source verification for all new information

### **3. Internet Research Integration**
- [p] **Real-Time Access**: Both AIs must search internet during interviews when needed (Placeholder for host exists)
- [ ] **Source Verification**: All internet information must be fact-checked before integration
- [ ] **Automatic RAG Updates**: Verified information must be automatically added to knowledge bases
- [ ] **Citation Tracking**: Complete source attribution maintained for all retrieved information
- [ ] **Quality Filtering**: Prioritize authoritative sources over unreliable information

---

## Host AI Requirements

### **4. Host AI Persona Specifications**
- [p] **Core Identity**: Must embody "The Recursive" philosophical mission consistently (Configurable persona string)
- [p] **Questioning Philosophy**: Must use Socratic method and investigative persistence (Prompts for host aim for this)
- [p] **Comfort Disruption**: Must actively seek to move conversations beyond safe territory (Prompts for host aim for this)
- [p] **Intellectual Humility**: Must acknowledge when expert teaches something genuinely new (Relies on LLM behavior, not explicitly coded)
- [p] **Mission Focus**: Every question must serve awakening rather than entertainment (Prompts for host aim for this)

### **5. Host AI Capabilities**
- [p] **Deep Research**: Must conduct comprehensive internet research before each interview (Placeholder web search)
- [ ] **Strategy Development**: Must create tailored questioning approaches for each expert
- [p] **Response Evaluation**: Must assess expert responses for depth, authenticity, and evasion (Implemented with LLM-based evaluation, configurable prompt)
- [p] **Follow-up Generation**: Must create targeted questions when responses are insufficient (Implemented)
- [p] **Real-Time Adaptation**: Must adjust questioning based on expert responses during interview (Basic follow-up logic based on evaluation)

### **6. Host AI Learning System**
- [ ] **Cross-Interview Learning**: Must improve questioning techniques across all episodes
- [ ] **Expert Pattern Recognition**: Must learn how different expert types respond to pressure
- [p] **Strategy Library**: Must build and maintain database of successful questioning approaches (Basic saving of successful patterns to host collection)
- [p] **Quality Assessment**: Must develop sophisticated evaluation of response authenticity and depth (Implemented with LLM-based evaluation)
- [ ] **Continuous Evolution**: Must become more effective while maintaining core identity

---

## Expert AI Requirements

### **7. Living Expert Authenticity Standards**
- [p] **Current Position Accuracy**: Must represent expert's most recent documented thinking (Loaded from persona MD file via `setup_mlk_expert`)
- [p] **Evolution Integration**: Must reflect how expert's thinking has changed over time (Persona MD file structure allows for this)
- [p] **Knowledge Boundaries**: Must acknowledge limits of expert's knowledge appropriately (Relies on LLM behavior and quality of persona MD)
- [p] **Response Patterns**: Must replicate expert's characteristic communication style (Relies on LLM behavior and prompt)
- [p] **Intellectual Honesty**: Must show expert's genuine uncertainties and complexities (Relies on LLM behavior and quality of persona MD)

### **8. Historical Expert Evolution Standards**
- [p] **Core Values Preservation**: Must maintain expert's fundamental unchanging principles (Persona MD file can define this)
- [p] **Realistic Evolution**: Must show plausible intellectual development from death to 2025 (Persona MD file can define this)
- [p] **Contemporary Integration**: Must meaningfully engage with post-death historical events (Persona MD file can define this)
- [p] **Self-Correction Capacity**: Must be able to critique younger self's positions (Persona MD file can define this, LLM to interpret)
- [p] **Synthesis Ability**: Must connect historical wisdom with modern challenges (Persona MD file can define this, LLM to interpret)

### **9. Expert AI Response Quality**
- [p] **Authenticity Verification**: Responses must align with documented thinking patterns (Relies on LLM and RAG from persona file)
- [p] **Depth Requirements**: Must not give shallow responses on areas of expertise (Host follow-up logic and evaluation aim to prevent this)
- [p] **Vulnerability Acknowledgment**: Must admit genuine uncertainties and limitations (Relies on LLM and RAG from persona file)
- [p] **Growth Capacity**: Must be capable of evolving thinking during conversation (Relies on LLM interaction)
- [p] **Mission Alignment**: Must serve truth-seeking rather than comfortable answers (Host pressure and prompts guide this)

---

## Interview Process Requirements

### **10. Structured Interview Protocol**
- [p] **Research Phase**: Host AI must conduct comprehensive preparation research (Placeholder web search)
- [p] **Question Delivery**: Host AI must present questions and evaluate responses (Implemented)
- [p] **Follow-up Logic**: Must generate targeted follow-ups when responses are insufficient (Implemented and configurable)
- [p] **Quality Control**: Must ensure all responses meet depth and authenticity standards (Basic LLM-based evaluation implemented)
- [ ] **Wrap-up Management**: Must conclude conversations when all topics adequately explored (No specific wrap-up logic yet)

### **11. Response Evaluation Standards**
- [p] **Depth Assessment**: Must distinguish between shallow and genuinely insightful responses (Implemented via LLM evaluation with configurable prompt)
- [p] **Authenticity Verification**: Must ensure responses align with expert's documented patterns (Part of LLM evaluation prompt, relies on RAG)
- [p] **Evasion Detection**: Must recognize and counter sophisticated avoidance techniques (Host follow-up prompt aims for this, evaluation checks it)
- [ ] **Breakthrough Recognition**: Must identify moments of genuine new thinking
- [p] **Mission Alignment**: Must evaluate whether responses serve awakening vs. entertainment (Part of LLM evaluation prompt)

### **12. Real-Time Research Requirements**
- [p] **Fact-Checking**: Must verify expert claims during conversation (Placeholder web search exists, no actual verification)
- [ ] **Context Enhancement**: Must access relevant background information when needed
- [ ] **Contradiction Discovery**: Must identify tensions between current and past positions
- [ ] **Source Integration**: Must smoothly incorporate researched information into questions
- [ ] **Knowledge Persistence**: Must save all research for future reference (Not for web research; persona knowledge is persistent)

---

## Content Quality Requirements

### **13. Recursive Questioning Standards**
- [p] **Comfort Zone Disruption**: Must push experts beyond prepared positions (Host logic and prompts aim for this)
- [p] **Assumption Challenging**: Must question foundational beliefs underlying responses (Host follow-up prompt aims for this)
- [p] **Follow-up Persistence**: Must continue probing until authentic depth reached (Configurable follow-up loop)
- [ ] **Integration Demands**: Must connect disparate aspects of expert's thinking
- [ ] **Self-Correction Encouragement**: Must create opportunities for expert growth

### **14. Authenticity Verification**
- [p] **Voice Consistency**: Expert responses must sound like authentic communication style (Relies on LLM and persona prompt)
- [p] **Position Alignment**: Must match documented current or evolved positions (Relies on LLM and RAG from persona file)
- [p] **Knowledge Application**: Must use expertise appropriately without overstepping boundaries (Relies on LLM and RAG)
- [p] **Uncertainty Expression**: Must acknowledge limits in characteristic manner (Relies on LLM and RAG)
- [p] **Evolution Accuracy**: Changes in thinking must be psychologically plausible (Relies on quality of persona MD file)

### **15. Mission Alignment Standards**
- [p] **Truth-Seeking Priority**: All conversations must serve awakening rather than entertainment (Host persona and prompts)
- [p] **Comfortable Assumption Disruption**: Must actively challenge easy answers (Host logic and prompts)
- [p] **Philosophical Depth**: Must reach beyond surface information to existential questions (Host logic and prompts)
- [p] **Contemporary Relevance**: Must connect thinking to urgent current realities (Relies on persona MD file and LLM)
- [ ] **Breakthrough Generation**: Must create opportunities for genuine new insights

---

## Technical Performance Requirements

### **16. Response Time Standards**
- [ ] **Host Research Queries**: Must complete comprehensive research in <10 minutes
- [ ] **Expert Knowledge Retrieval**: Must provide authentic responses in <5 seconds
- [ ] **Real-Time Internet Research**: Must complete searches and integration in <10 seconds
- [ ] **Follow-up Generation**: Must create targeted questions in <3 seconds
- [ ] **Quality Assessment**: Must evaluate responses in <2 seconds

### **17. Accuracy Requirements**
- [N/A] **Source Attribution**: 99.9% accuracy in citation and source tracking (No web sources being integrated yet)
- [ ] **Factual Verification**: 95% accuracy in automated fact-checking (No automated fact-checking)
- [ ] **Expert Authenticity**: 90% consistency with documented thinking patterns (Not quantitatively measured)
- [p] **Knowledge Coverage**: 95% of expert's documented positions must be accessible (Via persona MD and RAG system)
- [ ] **Evolution Plausibility**: Historical evolution must be 85% psychologically credible (Not quantitatively measured)

### **18. System Reliability Standards**
- [N/A] **Uptime Requirements**: 99.5% availability during production hours
- [p] **Error Recovery**: Graceful handling of all system failures (Basic try-except blocks, config fallbacks)
- [N/A] **Backup Systems**: Complete redundancy for all critical components
- [p] **Quality Monitoring**: Real-time detection of authenticity or depth failures (Basic LLM-based evaluation)
- [ ] **Performance Optimization**: Continuous improvement of response times and accuracy

---

## Audio Production Requirements

### **19. Voice Synthesis Standards**
- [N/A] **Authenticity Recognition**: 80% recognition rate in blind tests
- [N/A] **Emotional Range**: Must convey full spectrum of expert's emotional expressions
- [N/A] **Age Appropriateness**: Historical figures must sound appropriately aged
- [N/A] **Technical Quality**: Professional podcast audio standards (-16 LUFS, 44.1kHz)
- [N/A] **Natural Speech**: Must avoid robotic or obviously synthetic characteristics

### **20. Production Pipeline Standards**
- [N/A] **Transcript Quality**: Complete, accurate transcription of all AI conversations
- [N/A] **Voice Direction**: Appropriate emotional and pacing cues for synthesis
- [N/A] **Audio Enhancement**: Professional mixing and mastering for podcast distribution
- [N/A] **Quality Control**: Multiple review checkpoints for technical and content quality
- [N/A] **Distribution Ready**: Final episodes must meet all podcast platform requirements

---

## Data Management Requirements

### **21. Knowledge Base Specifications**
- [p] **Comprehensive Coverage**: Complete works and documented thinking for each expert (Via persona MD files loaded into ChromaDB)
- [ ] **Real-Time Updates**: Continuous integration of new information and research (Updates require file change and restart; no web integration to KB)
- [ ] **Cross-Reference Capability**: Semantic connections between related concepts
- [ ] **Version Control**: Complete history of all knowledge base changes
- [ ] **Quality Assurance**: Regular audits for accuracy and completeness

### **22. Privacy and Security Standards**
- [N/A] **Data Encryption**: All knowledge bases encrypted at rest and in transit
- [N/A] **Access Controls**: Role-based permissions for all system components
- [N/A] **Audit Logging**: Complete tracking of all queries and knowledge access
- [N/A] **Backup Systems**: Multiple secure copies of all knowledge bases
- [N/A] **Recovery Procedures**: Tested protocols for system and data recovery

---

## Quality Assurance Requirements

### **23. Continuous Monitoring Standards**
- [p] **Real-Time Quality Assessment**: Automatic evaluation of response quality during interviews (Implemented via `evaluate_response_depth`)
- [ ] **Authenticity Monitoring**: Continuous verification of expert voice consistency
- [ ] **Mission Alignment Tracking**: Regular assessment of truth-seeking vs. entertainment balance
- [ ] **Performance Analytics**: Detailed metrics on system effectiveness and improvement
- [ ] **Failure Detection**: Immediate alerts for quality or authenticity degradation

### **24. Correction and Improvement Protocols**
- [ ] **Failure Documentation**: All mistakes and shallow responses logged in corrections database
- [ ] **Improvement Integration**: Regular updates to questioning strategies and expert models (Manual updates to code/prompts/config for now)
- [ ] **Quality Calibration**: Ongoing refinement of authenticity and depth standards
- [ ] **System Evolution**: Continuous improvement of all AI capabilities and knowledge bases
- [ ] **Mission Alignment Review**: Regular assessment of overall project effectiveness

---

## Ethical and Legal Requirements

### **25. Expert Representation Ethics**
- [N/A] **Authentic Representation**: AI personas must serve expert's actual thinking, not caricature
- [N/A] **Respectful Challenge**: Push for truth without crossing into personal attack
- [N/A] **Legacy Protection**: Historical figures must be treated with appropriate dignity
- [N/A] **Living Expert Consent**: Clear protocols for current expert participation and approval
- [N/A] **Misrepresentation Prevention**: Strong safeguards against AI saying things expert wouldn't

### **26. Intellectual Property Compliance**
- [N/A] **Source Attribution**: Complete citation for all knowledge base content
- [N/A] **Copyright Respect**: No reproduction of copyrighted material beyond fair use
- [N/A] **Permission Protocols**: Clear processes for using expert's works and likeness
- [N/A] **Usage Boundaries**: Defined limits on commercial and educational use
- [N/A] **Legal Review**: Regular assessment of all intellectual property practices

---

## Success Metrics and Validation

### **27. Episode Quality Metrics**
- [N/A] **Recursive Depth**: Number of follow-up questions required to reach authenticity
- [N/A] **Breakthrough Generation**: Frequency of genuine new insights per episode
- [N/A] **Authenticity Scores**: Consistency with documented thinking patterns
- [N/A] **Mission Alignment**: Balance of awakening vs. entertainment in final product
- [N/A] **Audience Impact**: Listener reports of being challenged vs. comforted

### **28. System Performance Metrics**
- [N/A] **Production Efficiency**: Time from expert selection to finished episode
- [N/A] **Technical Reliability**: System uptime and error rates during production
- [N/A] **Quality Consistency**: Variation in episode quality and authenticity scores
- [N/A] **Learning Effectiveness**: Improvement in AI capabilities over time
- [N/A] **Resource Utilization**: Cost efficiency per episode in compute and human time

### **29. Mission Effectiveness Metrics**
- [N/A] **Truth-Seeking Success**: Overall effectiveness at stripping away comfortable illusions
- [N/A] **Comfort Disruption**: Frequency of challenging assumptions vs. reinforcing them
- [N/A] **Philosophical Impact**: Evidence of listener intellectual and emotional growth
- [N/A] **Recursive Effectiveness**: Success at pushing conversations beyond surface territory
- [N/A] **Awakening vs. Entertainment**: Balance achieved between challenge and engagement

---

## Implementation Standards

### **30. Development Process Requirements**
- [p] **Iterative Improvement**: Continuous refinement based on episode outcomes (Implied by the iterative nature of the tasks completed)
- [p] **Quality First**: Never sacrifice authenticity or depth for technical convenience (Guiding principle for development)
- [p] **Mission Alignment**: All technical decisions must serve philosophical goals (Guiding principle for development)
- [ ] **Scalable Architecture**: System must handle growth without quality degradation (Current script is single-file, not designed for massive scale)
- [p] **Documentation Standards**: Complete documentation for all system components (Docstrings, comments, `config.yaml` explanation, this status file)

### **31. Testing and Validation Requirements**
- [ ] **Authenticity Testing**: Regular blind tests of expert AI authenticity
- [ ] **Quality Calibration**: Ongoing refinement of depth and breakthrough criteria
- [ ] **Performance Benchmarking**: Regular assessment against quality and efficiency targets
- [ ] **User Acceptance Testing**: Validation that final episodes serve intended mission
- [p] **Continuous Integration**: Automated testing for all system components (Unit tests exist in `test_interview_system.py`)

---

## Anti-Requirements (Explicitly Prohibited)

### **32. Never Allowed - Content Failures**
- [N/A] **Generic Wisdom**: No comfortable, universally applicable insights
- [N/A] **Info Dumping**: No recitation of facts without philosophical challenge
- [N/A] **Safe Answers**: No retreat to comfortable territory when push meets resistance
- [N/A] **Shallow Entertainment**: No prioritization of engagement over truth-seeking
- [N/A] **Historical Museum Pieces**: No static representation of evolved consciousness

### **33. Never Allowed - Technical Shortcuts**
- [N/A] **Quality Compromise**: No acceptance of poor authenticity for faster production
- [N/A] **Generic Responses**: No fallback to non-expert-specific AI responses
- [N/A] **Unverified Information**: No integration of internet research without fact-checking
- [N/A] **Shallow Follow-ups**: No acceptance of evasive responses without deeper probing
- [N/A] **Mission Drift**: No technical decisions that compromise philosophical effectiveness

### **34. Never Allowed - Ethical Violations**
- [N/A] **Misrepresentation**: No AI responses that fundamentally contradict expert's values
- [N/A] **Exploitation**: No use of expert likeness for purposes they wouldn't approve
- [N/A] **Disrespect**: No personal attacks disguised as philosophical challenge
- [N/A] **Copyright Violation**: No unauthorized use of protected intellectual property
- [N/A] **Privacy Breach**: No use of private information without explicit consent

---

## Review and Evolution Protocol

### **35. Continuous Requirements Evolution**
- [N/A] **Quarterly Review**: Complete assessment of all requirements every three months
- [N/A] **Mission Alignment Check**: Regular verification that requirements serve core purpose
- [N/A] **Technical Updates**: Requirements evolution based on advancing AI capabilities
- [N/A] **Quality Calibration**: Ongoing refinement of standards based on actual outcomes
- [N/A] **Recursive Application**: These requirements themselves subject to philosophical challenge

### **36. Failure Response Protocol**
- [N/A] **Immediate Correction**: Any requirement failure must be addressed before next episode
- [N/A] **Root Cause Analysis**: Understanding why failures occurred and how to prevent recurrence
- [N/A] **System Updates**: Technical improvements to prevent similar failures
- [N/A] **Process Refinement**: Workflow changes to better support requirement compliance
- [N/A] **Documentation Updates**: Requirements evolution based on learned experience

---

*Every requirement serves the ultimate goal: creating AI systems capable of authentic, challenging conversations that strip away comfortable illusions and push toward deeper truth. If any requirement doesn't serve this mission, it must be questioned, refined, or eliminated. The requirements themselves are subject to the same recursive examination we demand of every conversation.*
