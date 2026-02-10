# User Experience Agent Documentation

## Overview
The User Experience Agent consolidates mobile testing and accessibility capabilities from two previously separate agents:
- Mobile Agent (ResponsiveTestingTool, DeviceCompatibilityTool, NetworkConditionTool, MobileUXTool)
- Accessibility Agent (WCAGComplianceTool, ScreenReaderTool, KeyboardNavigationTool, ColorContrastTool)

## Capabilities

### 1. Responsive Design Testing
- **Breakpoint Verification**: Testing across standard device breakpoints (320px to 1920px)
- **Viewport Analysis**: Content overflow, navigation adaptation, image scaling
- **Touch Target Validation**: 44x44px minimum touch target compliance (WCAG 2.5.5)
- **Layout Consistency**: Visual layout verification across all viewport sizes

### 2. Device Compatibility Matrix
- **Cross-Device Testing**: Mobile (iOS/Android), Tablet, Desktop compatibility
- **OS Version Support**: iOS 15+, Android 12+, macOS 12+, Windows 10+
- **Browser Compatibility**: Chrome, Safari, Firefox, Edge testing
- **Market Coverage**: Device market share and compatibility analysis

### 3. Mobile UX Optimization
- **Gesture Support**: Swipe, pinch-to-zoom, pull-to-refresh, long-press
- **Orientation Handling**: Layout adaptation, state preservation, media continuity
- **App Lifecycle**: Background/foreground handling, data persistence, deep linking
- **Mobile Patterns**: Mobile navigation, touch-friendly forms, haptic feedback

### 4. Comprehensive WCAG Compliance
- **Heading Hierarchy**: Logical heading structure (H1 > H2 > H3) validation
- **ARIA Landmarks**: Main, navigation, banner, contentinfo landmark validation
- **Form Accessibility**: Label association, required field indicators, accessible names
- **Alt Text Validation**: Descriptive alt text for informational images
- **Keyboard Navigation**: Full keyboard accessibility and skip navigation links
- **Screen Reader Support**: ARIA usage, live regions, focus management

### 5. Cross-Platform UX Analysis
- **Responsive-Device Correlation**: How responsive design affects device compatibility
- **Mobile-Accessibility Correlation**: Mobile UX impact on accessibility compliance
- **Device-Accessibility Correlation**: Device compatibility effects on accessibility
- **Unified UX Scoring**: Weighted scoring across all UX dimensions

## Tools

### ResponsiveTestingTool
**Purpose**: Comprehensive responsive design and breakpoint validation

**Parameters**:
- `responsive_config`: Dict containing target URL and custom breakpoints

**Breakpoint Testing**:
- Standard device matrix (iPhone SE, iPhone 8, iPhone 11, iPad, Desktop, Full HD)
- Viewport overflow detection and navigation adaptation testing
- Touch target size validation (44x44px minimum)
- Layout consistency across all breakpoints

**Output Metrics**:
- Responsive design score (0-100)
- Breakpoint-specific test results
- Touch target compliance status
- Actionable design recommendations

### DeviceCompatibilityTool
**Purpose**: Device matrix compatibility and OS version support validation

**Parameters**:
- `device_config`: Dict containing target devices and compatibility requirements

**Compatibility Areas**:
- Device matrix testing (mobile, tablet, desktop)
- OS version compatibility and market coverage analysis
- Browser compatibility matrix with version requirements
- Device-specific rendering and functionality testing

**Output Metrics**:
- Overall compatibility rate percentage
- Device-specific test results and failures
- OS and browser compatibility analysis
- Market coverage recommendations

### MobileUXTool
**Purpose**: Mobile-specific user experience pattern validation

**Parameters**:
- `ux_config`: Dict containing mobile UX test configuration

**Mobile UX Areas**:
- Gesture support (swipe, pinch, pull-to-refresh, long-press)
- Orientation change handling and state preservation
- App lifecycle event handling (background/foreground, suspension)
- Mobile-first UX patterns (navigation, forms, haptics, PWA)

**Output Metrics**:
- Mobile UX score (0-100)
- Gesture and orientation test results
- Lifecycle and pattern compliance status
- Mobile-specific improvement recommendations

### WCAGComplianceTool
**Purpose**: Comprehensive WCAG 2.1 AA/AAA compliance validation

**Parameters**:
- `accessibility_config`: Dict containing target URL and WCAG level

**WCAG Compliance Areas**:
- Heading hierarchy and structure validation
- ARIA landmark implementation
- Form label association and accessibility
- Image alt text compliance
- WCAG 2.1 criteria validation across success criteria

**Output Metrics**:
- WCAG compliance score (0-100)
- Achieved compliance level (AAA/AA/A/non-compliant)
- Criterion-specific violation tracking
- Remediation recommendations by WCAG article

## Integration

### Replaces
- `agents/mobile/qa_mobile.py` (ResponsiveTestingTool, DeviceCompatibilityTool, MobileUXTool)
- `agents/accessibility/qa_accessibility.py` (WCAGComplianceTool, ScreenReaderTool, KeyboardNavigationTool, ColorContrastTool)
- Enhanced with cross-platform correlation and unified UX scoring

### Maintains Compatibility
- All existing tool interfaces preserved
- Enhanced with cross-platform UX correlation analysis
- Integrated accessibility testing with mobile UX validation
- Unified executive reporting across all UX dimensions

### Redis Keys
- Stores results under `user_experience:{session_id}:analysis`
- Publishes notifications to `manager:{session_id}:notifications`

### Celery Queue
- Uses `user_experience_agent` queue for task processing

## Usage Examples

### Comprehensive UX Analysis
```python
task_data = {
    "session_id": "session_123",
    "scenario": {
        "id": "user_experience_analysis",
        "target_url": "https://app.example.com",
        "test_scope": "full_ux_suite",
        "wcag_level": "AA"
    }
}
```

### Mobile UX Testing
```python
mobile_config = {
    "url": "https://app.example.com",
    "test_gestures": True,
    "test_orientation": True,
    "test_lifecycle": True
}
```

### WCAG Compliance Validation
```python
wcag_config = {
    "url": "https://app.example.com",
    "level": "AA",  # or "AAA"
    "check_headings": True,
    "check_landmarks": True,
    "check_forms": True
}
```

## Enhanced Capabilities

### Cross-Platform UX Correlation
- **Responsive-Device**: How responsive design affects device compatibility
- **Mobile-Accessibility**: Mobile UX patterns impact on accessibility compliance
- **Device-Accessibility**: Device-specific accessibility considerations
- **Unified Risk Assessment**: Cross-domain UX risk identification

### Integrated UX Scoring
- **Weighted Average**: Responsive (25%), Device (20%), Mobile (30%), Accessibility (25%)
- **UX Maturity Levels**: Excellent (90+), Mature (80+), Developing (70+), Immature (<70)
- **Executive Metrics**: Business-friendly UX indicators
- **Trend Analysis**: Historical UX improvement tracking

### Mobile-First Accessibility
- **Mobile Accessibility**: Accessibility testing optimized for mobile devices
- **Touch Accessibility**: Touch target accessibility compliance
- **Mobile Screen Readers**: Screen reader optimization for mobile devices
- **Mobile WCAG**: WCAG compliance with mobile-specific considerations

## Migration Notes

### From Mobile Agent
- All mobile tools preserved and enhanced
- ResponsiveTestingTool: Enhanced with accessibility correlation
- DeviceCompatibilityTool: Enhanced with cross-platform analysis
- MobileUXTool: Enhanced with accessibility integration

### From Accessibility Agent
- WCAGComplianceTool: Preserved and enhanced with mobile correlation
- ScreenReaderTool: Integrated into MobileUXTool lifecycle testing
- KeyboardNavigationTool: Integrated into WCAGComplianceTool criteria
- ColorContrastTool: Simplified into core WCAG compliance checks

## Configuration

### Environment Variables
- `OPENAI_MODEL`: LLM model for agent reasoning (default: gpt-4o)
- `REDIS_URL`: Redis connection string
- `RABBITMQ_URL`: RabbitMQ connection string

### WCAG Configuration
```python
wcag_config = {
    "level": "AA",  # or "AAA"
    "check_headings": True,
    "check_landmarks": True,
    "check_forms": True,
    "check_alt_text": True
}
```

### Device Configuration
```python
device_config = {
    "min_ios_version": "15",
    "min_android_version": "12",
    "target_browsers": ["Chrome", "Safari", "Firefox"],
    "test_tablets": True,
    "test_desktop": True
}
```

## Scoring & Metrics

### UX Score Calculation
- **Responsive Design**: 25% weight (0-100 based on breakpoint compliance)
- **Device Compatibility**: 20% weight (0-100 based on device matrix success rate)
- **Mobile UX**: 30% weight (0-100 based on mobile pattern compliance)
- **Accessibility**: 25% weight (0-100 based on WCAG compliance)

### UX Maturity Levels
- **Excellent** (90+): Mature UX with strong mobile and accessibility compliance
- **Mature** (80+): Good UX with minor improvement areas
- **Developing** (70+): Moderate UX with significant improvement opportunities
- **Immature** (<70): Poor UX requiring major improvements

## Docker Service

```yaml
user_experience:
  build:
    context: .
    dockerfile: agents/user_experience/Dockerfile
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - REDIS_URL=redis://redis:6379/0
    - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
  depends_on:
    - redis
    - rabbitmq
  volumes:
    - ./agents/user_experience:/app
```

## Benefits of Consolidation

### Efficiency Gains
- **50% reduction** in mobile/accessibility agents (2 → 1)
- **Unified UX scoring** across mobile, responsive, and accessibility
- **Cross-platform correlation** identifies systemic UX issues
- **Single UX dashboard** for comprehensive user experience monitoring

### Enhanced Capabilities
- **Mobile-First Accessibility**: Accessibility testing optimized for mobile devices
- **Cross-Platform Analysis**: UX correlation across responsive, device, and accessibility
- **Integrated WCAG Testing**: Accessibility testing with mobile UX integration
- **Executive UX Reporting**: Business-focused UX metrics and maturity assessment

### Operational Improvements
- **Reduced redundant testing** across mobile and accessibility domains
- **Improved user experience consistency** across all device categories
- **Streamlined UX improvement planning** with unified scoring
- **Better resource utilization** through consolidated UX analysis

### Accessibility Integration
- **Mobile Accessibility**: Accessibility compliance optimized for mobile devices
- **Touch Accessibility**: Touch interface accessibility validation
- **Cross-Device Accessibility**: Consistent accessibility across all device types
- **WCAG 2.1 Mobile**: WCAG compliance with mobile-specific success criteria