import streamlit as st
import pandas as pd
import json
from datetime import datetime
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Material Data (your existing data)
Material_detailes = {
    "Steel": {"Fatigue constant": 3, "youngs Modulus": 0.205},
    "Aluminum": {"Fatigue constant": 5, "youngs Modulus": 0.07},
}

# Calculator Functions (your existing functions)
def panic_brake_calculation(inputs):
    force = inputs["Mass of the Vehicle (kg)"] * inputs["Max Deceleration (m/s^2)"]
    torque = force * inputs["Tyre rolling radius (m)"]
    applied_force = (torque / inputs["Fixture arm length (m)"]) / 9.81
    total_cycles = inputs["Total life (km)"] / inputs["Road to rig factor"]
    return {"Required Load (kg)": applied_force, "Required Cycles": total_cycles}

def Front_Fork_Fatigue_calculation(inputs):
    Max_BM = inputs["fork Length (mm)"] * inputs["Max Load (kgf)"]
    Min_BM = inputs["fork Length (mm)"] * inputs["Min Load (kgf)"]
    Max_strain = (Max_BM * inputs["Calibration factor"]) + inputs["Calibration constant"]
    Min_strain = (Min_BM * inputs["Calibration factor"]) + inputs["Calibration constant"]

    Material_type = inputs["Material"]
    Material_data = Material_detailes[Material_type]

    Max_stress = Max_strain * Material_data["youngs Modulus"]
    Min_stress = Min_strain * Material_data["youngs Modulus"]
    Mean_stress = (Max_stress + Min_stress) / 2
    Amplitude_stress = (Max_stress - Min_stress) / 2
    Mean_corrected_stress = Amplitude_stress / (1 - (Mean_stress / Amplitude_stress))

    Damage_per_cycle = Mean_corrected_stress ** Material_data["Fatigue constant"]
    Number_of_Cycles = (inputs["Target Damage"] * inputs["Factor of Safety"]) / Damage_per_cycle

    return {"Total Number of cycles": Number_of_Cycles}

# Test Definitions (your existing config)
test_definitions = {
    "Panic Brake Fatigue": {
        "inputs": {
            "Max Deceleration (m/s^2)": {"type": "number", "min_value": 1.0},
            "Mass of the Vehicle (kg)": {"type": "number", "min_value": 1.0},
            "Tyre rolling radius (m)": {"type": "number", "value": 1.0},
            "Fixture arm length (m)": {"type": "number", "value": 1.0},
            "Total life (km)": {"type": "number", "min_value": 1.0},
            "Road to rig factor": {"type": "number", "value": 1.0},
        },
        "calculator": panic_brake_calculation
    },
    "Front Fork Fatigue": {
        "inputs": {
            "Target Damage": {"type": "number", "value": 1.0},
            "fork Length (mm)": {"type": "number", "value": 1.0},
            "Max Load (kgf)": {"type": "number", "value": 1.0},
            "Min Load (kgf)": {"type": "number", "value": 1.0},
            "Calibration factor": {
                "type": "number", "value": 0.00054,
                "min_value": 0.00001,
                "step": 0.00001, "format": "%.8f"
            },
            "Calibration constant": {"type": "number", "value": -1.356, "step": 0.001, "format": "%.5f"},
            "Material": {"type": "selectbox", "options": list(Material_detailes.keys())},
            "Factor of Safety": {"type": "number", "value": 1.0},
        },
        "calculator": Front_Fork_Fatigue_calculation
    }
}

# === NEW: Excel Export Function ===
def create_excel_report(test_name, inputs, results):
    """Create a professional Excel report with formatting"""

    # Create workbook and worksheet
    output = BytesIO()
    workbook = openpyxl.Workbook()
    ws = workbook.active
    ws.title = "Test Specification Report"

    # Define styles
    header_font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

    subheader_font = Font(name="Arial", size=12, bold=True, color="FFFFFF")
    subheader_fill = PatternFill(start_color="5B9BD5", end_color="5B9BD5", fill_type="solid")

    regular_font = Font(name="Arial", size=10)
    bold_font = Font(name="Arial", size=10, bold=True)

    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    # Header Section
    ws.merge_cells("A1:D1")
    ws["A1"] = "TEST SPECIFICATION CALCULATION REPORT"
    ws["A1"].font = header_font
    ws["A1"].fill = header_fill
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 25

    # Test Information Section
    row = 3
    ws.merge_cells(f"A{row}:D{row}")
    ws[f"A{row}"] = "TEST INFORMATION"
    ws[f"A{row}"].font = subheader_font
    ws[f"A{row}"].fill = subheader_fill
    ws[f"A{row}"].alignment = Alignment(horizontal="center")

    row += 1
    test_info = [
        ["Test Type:", test_name],
        ["Calculation Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Generated By:", "Automated Test Spec Calculator"],
        ["Version:", "2.0"]
    ]

    for info in test_info:
        ws[f"A{row}"] = info[0]
        ws[f"A{row}"].font = bold_font
        ws[f"B{row}"] = info[1]
        ws[f"B{row}"].font = regular_font
        row += 1

    # Input Parameters Section
    row += 1
    ws.merge_cells(f"A{row}:D{row}")
    ws[f"A{row}"] = "INPUT PARAMETERS"
    ws[f"A{row}"].font = subheader_font
    ws[f"A{row}"].fill = subheader_fill
    ws[f"A{row}"].alignment = Alignment(horizontal="center")

    row += 1
    ws[f"A{row}"] = "Parameter"
    ws[f"B{row}"] = "Value"
    ws[f"C{row}"] = "Unit"
    ws[f"D{row}"] = "Notes"

    for col in ["A", "B", "C", "D"]:
        ws[f"{col}{row}"].font = bold_font
        ws[f"{col}{row}"].fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

    row += 1
    for param, value in inputs.items():
        ws[f"A{row}"] = param
        if isinstance(value, float):
            ws[f"B{row}"] = f"{value:.6f}"
        else:
            ws[f"B{row}"] = str(value)
        ws[f"C{row}"] = ""  # Unit column - can be enhanced later
        ws[f"D{row}"] = ""  # Notes column
        row += 1

    # Results Section
    row += 1
    ws.merge_cells(f"A{row}:D{row}")
    ws[f"A{row}"] = "CALCULATION RESULTS"
    ws[f"A{row}"].font = subheader_font
    ws[f"A{row}"].fill = subheader_fill
    ws[f"A{row}"].alignment = Alignment(horizontal="center")

    row += 1
    ws[f"A{row}"] = "Result Parameter"
    ws[f"B{row}"] = "Calculated Value"
    ws[f"C{row}"] = "Unit"
    ws[f"D{row}"] = "Status"

    for col in ["A", "B", "C", "D"]:
        ws[f"{col}{row}"].font = bold_font
        ws[f"{col}{row}"].fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

    row += 1
    for param, value in results.items():
        ws[f"A{row}"] = param
        if isinstance(value, float):
            ws[f"B{row}"] = f"{value:.6f}"
        else:
            ws[f"B{row}"] = str(value)
        ws[f"C{row}"] = ""  # Unit
        ws[f"D{row}"] = "✓ Calculated"
        row += 1

    # Apply borders to all used cells
    for row_num in range(1, row):
        for col in ["A", "B", "C", "D"]:
            ws[f"{col}{row_num}"].border = border

    # Auto-adjust column widths
    column_widths = {
    'A': 25,  # Parameter names
    'B': 15,  # Values  
    'C': 10,  # Units
    'D': 20   # Notes/Status
    }

    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    # Save workbook
    workbook.save(output)
    return output.getvalue()

# === NEW: PDF Export Function ===
def create_pdf_report(test_name, inputs, results):
    """Create a professional PDF report"""

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
    story = []

    # Get styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.darkblue
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue,
        borderWidth=1,
        borderColor=colors.darkblue,
        borderPadding=5,
        backColor=colors.lightgrey
    )

    # Title
    title = Paragraph("TEST SPECIFICATION CALCULATION REPORT", title_style)
    story.append(title)
    story.append(Spacer(1, 20))

    # Test Information Section
    story.append(Paragraph("TEST INFORMATION", heading_style))

    test_info_data = [
        ["Test Type:", test_name],
        ["Calculation Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Generated By:", "Automated Test Spec Calculator"],
        ["Version:", "2.0"]
    ]

    test_info_table = Table(test_info_data, colWidths=[2*inch, 3*inch])
    test_info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))

    story.append(test_info_table)
    story.append(Spacer(1, 20))

    # Input Parameters Section
    story.append(Paragraph("INPUT PARAMETERS", heading_style))

    input_data = [["Parameter", "Value", "Unit"]]
    for param, value in inputs.items():
        if isinstance(value, float):
            formatted_value = f"{value:.6f}"
        else:
            formatted_value = str(value)
        input_data.append([param, formatted_value, ""])  # Unit column can be enhanced

    input_table = Table(input_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
    input_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))

    story.append(input_table)
    story.append(Spacer(1, 20))

    # Results Section
    story.append(Paragraph("CALCULATION RESULTS", heading_style))

    results_data = [["Result Parameter", "Calculated Value", "Unit", "Status"]]
    for param, value in results.items():
        if isinstance(value, float):
            formatted_value = f"{value:.6f}"
        else:
            formatted_value = str(value)
        results_data.append([param, formatted_value, "", "✓ Calculated"])

    results_table = Table(results_data, colWidths=[2*inch, 1.5*inch, 0.8*inch, 1.2*inch])
    results_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
    ]))

    story.append(results_table)
    story.append(Spacer(1, 30))

    # Footer
    footer_text = f"""
    <para alignment="center">
    <font size="8" color="grey">
    Generated by Automated Test Spec Calculator | 
    Report Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 
    Page 1 of 1
    </font>
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))

    # Build PDF
    doc.build(story)
    return buffer.getvalue()

# === Streamlit UI ===
st.set_page_config(
    page_title="Test Spec Calculator", 
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Automated Test Spec Calculation Tool")
st.markdown("---")

# Test Selection
selected_test = st.selectbox("🎯 Select Test Type", list(test_definitions.keys()))
test_config = test_definitions[selected_test]

# Create two columns for better layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📋 Input Parameters for: {selected_test}")
    inputs = {}

    # Dynamic input generation
    for label, config in test_config["inputs"].items():
        key = f"{selected_test}_{label}"
        if config["type"] == "number":
            inputs[label] = st.number_input(label, key=key, **{k: v for k, v in config.items() if k != "type"})
        elif config["type"] == "selectbox":
            inputs[label] = st.selectbox(label, config["options"], key=key)

    # Calculate button
    calculate_clicked = st.button("🚀 Calculate", type="primary", use_container_width=True)

with col2:
    st.subheader("📊 Results & Export")

    if calculate_clicked:
        try:
            # Perform calculation
            result = test_config["calculator"](inputs)

            # Store results in session state for download
            st.session_state['last_calculation'] = {
                'test_name': selected_test,
                'inputs': inputs,
                'results': result,
                'timestamp': datetime.now()
            }

            # Display results
            st.success("✅ Calculation Complete!")

            for k, v in result.items():
                if isinstance(v, float):
                    st.metric(label=k, value=f"{v:.6f}")
                else:
                    st.metric(label=k, value=str(v))

        except Exception as e:
            st.error(f"❌ Calculation Error: {str(e)}")
            st.error("Please check your input values and try again.")

# === NEW: Enhanced Download Section ===
if 'last_calculation' in st.session_state:
    st.markdown("---")
    st.subheader("📥 Export Report")

    calc_data = st.session_state['last_calculation']

    # Create download buttons
    download_col1, download_col2 = st.columns(2)

    with download_col1:
        # Excel Download
        try:
            excel_data = create_excel_report(calc_data['test_name'], calc_data['inputs'], calc_data['results'])
            st.download_button(
                label="📊 Download Excel Report",
                data=excel_data,
                file_name=f"{calc_data['test_name']}_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Professional Excel report with inputs and results",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Excel generation error: {e}")

    with download_col2:
        # PDF Download
        try:
            pdf_data = create_pdf_report(calc_data['test_name'], calc_data['inputs'], calc_data['results'])
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_data,
                file_name=f"{calc_data['test_name']}_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                help="Professional PDF report with complete documentation",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

# === Footer ===
st.markdown("---")
st.markdown("*Built with ❤️ using Streamlit | Version 2.1 with Excel & PDF Export*")

