# ADR-004: Report Generation Strategy

## Status
Accepted

## Context
The WebGUI needs to generate comprehensive reports including:
1. PDF reports with charts and professional formatting
2. JSON/CSV data exports for analysis
3. Custom report templates and branding
4. Scheduled and automated report generation
5. Large dataset handling with progress tracking
6. Multi-format support for different stakeholders

The system processes large amounts of test data that needs to be transformed into various output formats.

## Decision
We selected a **Template-Based Report Generation Architecture**:

- **ReportLab** - PDF generation with charts and graphics
- **Jinja2** - HTML templates for flexible report layouts
- **Pandas** - Data processing and CSV export
- **WeasyPrint** - HTML to PDF conversion for complex layouts
- **Background Task Queue** - Async report generation with progress tracking

## Consequences

### Positive
- **Flexibility**: Template-based approach allows easy customization
- **Performance**: Background generation doesn't block UI
- **Scalability**: Can handle large datasets with streaming
- **Multiple Formats**: Single data source, multiple output formats
- **Professional Quality**: High-quality PDF with charts and branding
- **Progress Tracking**: Real-time updates during long-running generations

### Negative
- **Complexity**: Multiple dependencies and template systems
- **Memory Usage**: Large datasets can be memory intensive
- **Learning Curve**: Team needs to learn ReportLab and Jinja2
- **Dependencies**: Additional system dependencies (WeasyPrint)

## Rationale

### Evaluation of Alternatives

1. **Simple PDF Libraries (FPDF, PyPDF2)**
   - Pros: Lightweight, simple to use
   - Cons: Limited formatting, no chart support
   
2. **LaTeX-Based Generation**
   - Pros: Professional typesetting, excellent for scientific reports
   - Cons: Complex, heavy dependencies, steep learning curve
   
3. **External Service Integration**
   - Pros: Offloads complexity, professional results
   - Cons: Cost, vendor lock-in, data privacy concerns
   
4. **Template-Based Architecture** (Selected)
   - Pros: Flexible, maintainable, good performance, professional results
   - Cons: More complex initial setup

### Report Generation Pipeline

```
Raw Test Data → Data Processing → Template Rendering → Format Output
                    ↓                 ↓              ↓
             Pandas/DuckDB      Jinja2/HTML    PDF/JSON/CSV
                    ↓                 ↓              ↓
               Aggregation      ChartGen      WeasyPrint/
                    ↓                 ↓              ↓
               Chart Data      CSS/Styling   ReportLab
```

### Template Strategy

**Base Templates:**
- `executive_summary.html` - High-level overview for stakeholders
- `technical_details.html` - Detailed results for engineers
- `compliance_report.html` - Regulatory and audit reports
- `comparison_report.html` - Session comparisons and trends

**Chart Generation:**
- Matplotlib/Plotly for static charts
- Chart.js for interactive HTML reports
- SVG embedding for vector graphics

### Data Flow

1. **Data Collection** - Gather test results from Redis/sessions
2. **Processing** - Aggregate, filter, and transform using Pandas
3. **Template Selection** - Choose template based on report type
4. **Rendering** - Apply data to Jinja2 templates
5. **Format Conversion** - Generate final output (PDF/HTML/CSV/JSON)
6. **Storage** - Save reports with metadata and access control

### Report Types

**Executive Dashboard:**
- Pass/fail rates, trends, risk metrics
- Interactive charts and drill-downs
- Summary for non-technical stakeholders

**Technical Report:**
- Detailed test results, error logs
- Performance metrics, regression analysis
- Recommendations and action items

**Compliance Report:**
- Audit trails, regulatory checklists
- Security assessments, accessibility results
- Formal documentation for compliance teams

## Implementation Notes

Key components:

1. **Report Engine** (`webgui/reports/engine.py`)
   - Template management and rendering
   - Chart generation and embedding
   - Multi-format output handling

2. **Data Processor** (`webgui/reports/data.py`)
   - Data aggregation and filtering
   - Statistical analysis and trends
   - Export format preparation

3. **Task Queue** (`webgui/reports/tasks.py`)
   - Background report generation
   - Progress tracking and notifications
   - Error handling and retry logic

The architecture supports scheduled reports, custom branding, and integration with external BI tools for advanced analytics.