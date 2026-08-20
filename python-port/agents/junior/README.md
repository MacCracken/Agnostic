# Junior QA Worker

## Overview
The Junior QA Worker executes regression test suites, generates synthetic test data, optimizes test execution order, and performs cross-platform testing across web, mobile, and desktop.

## Capabilities
- **Regression Testing**: Automated regression suite execution with root cause detection
- **Synthetic Data Generation**: Realistic test data using Faker with domain-aware generation
- **Test Execution Optimization**: Risk-based test ordering for faster feedback
- **Visual Regression**: Pixel-level comparison and baseline management
- **Mobile App Testing**: iOS/Android testing via Appium integration
- **Desktop App Testing**: Windows/macOS/Linux native and Electron app testing
- **Cross-Platform Orchestration**: Unified testing across web, mobile, and desktop

## Tools

### RegressionTestingTool
**Purpose**: Executes regression suites with Playwright for UI tests and pytest for backend tests

**Parameters**:
- `test_suite`: Test suite definition with test cases
- `environment`: Target environment (staging, production, etc.)

### SyntheticDataGeneratorTool
**Purpose**: Generates realistic test data for various scenarios

**Parameters**:
- `data_spec`: Specification of data types and volumes needed
- `locale`: Locale for region-specific data generation

### TestExecutionOptimizerTool
**Purpose**: Optimizes test execution order based on risk scores and code changes

**Parameters**:
- `test_cases`: List of test cases to prioritize
- `code_changes`: Recent code changes for risk calculation

### VisualRegressionTool
**Purpose**: Performs visual regression testing with baseline capture and pixel diffing

**Parameters**:
- `baseline_url`: URL of baseline page
- `comparison_url`: URL to compare against baseline
- `threshold`: Pixel difference tolerance

### MobileAppTestingTool
**Purpose**: iOS and Android testing using Appium

**Parameters**:
- `app_config`: Mobile app configuration (platform, device, app path)
- `test_scenarios`: Test scenarios to execute

### DesktopAppTestingTool
**Purpose**: Desktop application testing for Windows, macOS, and Linux

**Parameters**:
- `app_config`: Desktop app configuration (platform, app path)
- `test_scenarios`: Test scenarios to execute

### FlakyTestDetectionTool
**Purpose**: Intelligent flaky test identification with quarantine management and auto-retry strategies

**Parameters**:
- `test_suite`: Test suite to analyze for flakiness
- `history_window`: Number of past runs to analyze

### UXUsabilityTestingTool
**Purpose**: UX/usability testing with session analysis, heatmaps, A/B testing, and user journey validation

**Parameters**:
- `target_url`: URL of the application to test
- `test_scenarios`: UX test scenarios to execute

### LocalizationTestingTool
**Purpose**: Multi-language validation, RTL layout testing, timezone handling, and cultural formatting checks

**Parameters**:
- `target_url`: URL of the application to test
- `locales`: List of locales to validate

### CrossPlatformTestingTool
**Purpose**: Unified cross-platform testing orchestrator

**Parameters**:
- `platforms`: Target platforms (web, ios, android, windows, macos, linux)
- `test_scenarios`: Shared test scenarios

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
PRIMARY_MODEL_PROVIDER=openai
REDIS_HOST=localhost
REDIS_PORT=6379
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
```

## Development

### Testing
```bash
pytest tests/unit/test_junior_qa_tools.py
```

### Docker Service
```yaml
junior-qa:
  build:
    context: .
    dockerfile: agents/junior/Dockerfile
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - REDIS_HOST=redis
    - RABBITMQ_HOST=rabbitmq
  depends_on:
    - redis
    - rabbitmq
```

## Integration Points

### Redis Communication
- **Input Channels**: `junior:{session_id}:tasks`
- **Output Channels**: `junior:{session_id}:results`
- **Status Updates**: `junior:{session_id}:status`

### Delegation
Receives regression testing, data generation, and cross-platform testing tasks from the QA Manager. Tasks are typically lower complexity but higher volume.
