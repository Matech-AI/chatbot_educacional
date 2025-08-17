# Educational Agent Unit Tests

## Overview
This test suite provides comprehensive testing for the Educational Agent module, covering all major functionality including initialization, chat operations, learning context management, and API endpoints.

## Test Structure

### Test Files
- `test_educational_agent.py` - Main test suite for the Educational Agent
- `run_tests.py` - Script to run all tests with proper configuration

## Test Categories

### 1. Initialization Tests (`TestEducationalAgentInitialization`)
- Tests agent initialization with valid API keys
- Tests initialization without OpenAI key (RAG disabled)
- Tests Gemini to OpenAI fallback mechanism
- Tests error handling when no valid model is available

### 2. Learning Context Management (`TestLearningContextManagement`)
- Tests creating new learning contexts
- Tests retrieving existing contexts
- Tests updating context with new information
- Tests handling invalid attribute updates

### 3. Follow-up Questions (`TestFollowUpQuestions`)
- Tests question generation for different difficulty levels (beginner, intermediate, advanced)
- Tests fallback to default questions for invalid levels

### 4. Chat Functionality (`TestChatFunctionality`)
- Tests basic chat operations
- Tests chat with learning preferences
- Tests error handling during chat
- Tests chat without initialized graph

### 5. Learning Path (`TestLearningPath`)
- Tests learning path generation with documents
- Tests learning path generation without documents (fallback)
- Tests error handling when retriever is not initialized
- Tests LLM error handling with fallback paths

### 6. API Endpoints (`TestAPIEndpoints`)
- Tests educational chat endpoint
- Tests session context retrieval
- Tests learning path generation endpoint
- Tests adding topics to learning path
- Tests simple chat endpoint
- Tests topic exploration

### 7. Singleton Pattern (`TestSingletonPattern`)
- Tests that `get_educational_agent()` returns the same instance

### 8. System Prompt (`TestSystemPrompt`)
- Tests basic system prompt generation
- Tests prompt with learning objectives
- Tests prompt with knowledge gaps

### 9. Graph Building (`TestGraphBuilding`)
- Tests graph node structure
- Tests retriever node functionality

### 10. Integration Tests (`TestIntegrationFlow`)
- Tests complete learning session workflow
- Tests interaction between different components

## Running Tests

### Basic Usage
```bash
# Run all tests
python backend/tests/run_tests.py

# Run with pytest directly
pytest backend/tests/test_educational_agent.py -v

# Run specific test class
pytest backend/tests/test_educational_agent.py::TestChatFunctionality -v

# Run specific test
pytest backend/tests/test_educational_agent.py::TestChatFunctionality::test_chat_basic -v
```

### Test Coverage
```bash
# Run with coverage report
pytest backend/tests/test_educational_agent.py --cov=backend/chat_agents --cov-report=html
```

## Mocking Strategy

The test suite uses extensive mocking to isolate components:

### Key Mocks
1. **Environment Variables** - Mocked API keys for testing
2. **ChromaDB** - Mocked vector store and retriever
3. **LLM Models** - Mocked Gemini and OpenAI models
4. **Graph Execution** - Mocked graph ainvoke methods

### Fixtures
- `mock_env_vars` - Sets up test environment variables
- `mock_chroma_db` - Provides mocked ChromaDB instance
- `mock_llm_model` - Provides mocked LLM with structured output
- `educational_agent_instance` - Creates agent with all mocked dependencies

## Test Data

### Sample Documents
Tests use sample documents with fitness/training content:
- "Content about muscle hypertrophy and training"
- "Advanced training techniques for athletes"

### Sample Learning Paths
Default learning paths include:
- Introduction steps (easy difficulty)
- Advanced concepts (medium difficulty)

## Dependencies

Required packages for testing:
```bash
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
```

## Best Practices

1. **Isolation** - Each test is isolated with proper mocking
2. **Async Support** - Uses `pytest.mark.asyncio` for async tests
3. **Clear Naming** - Test names clearly describe what they test
4. **Comprehensive Coverage** - Covers happy paths and error scenarios
5. **Documentation** - Each test class and method has docstrings

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure backend directory is in Python path
   - Check that all dependencies are installed

2. **Async Test Failures**
   - Verify pytest-asyncio is installed
   - Use `@pytest.mark.asyncio` decorator

3. **Mock Failures**
   - Check mock patch paths are correct
   - Verify mock return values match expected types

## Future Improvements

1. Add performance benchmarks
2. Add stress testing for concurrent sessions
3. Add integration tests with real ChromaDB
4. Add mutation testing
5. Add property-based testing for edge cases

## Contributing

When adding new tests:
1. Follow existing naming conventions
2. Add appropriate fixtures if needed
3. Include both success and failure scenarios
4. Update this README with new test descriptions