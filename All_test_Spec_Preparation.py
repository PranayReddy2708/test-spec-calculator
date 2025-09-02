import streamlit as st
import pandas as pd
import json
from datetime import datetime
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Material Data
Material_detailes = {
    "Steel": {"Fatigue constant": 3, "youngs Modulus": 0.205},
    "Aluminum": {"Fatigue constant": 5, "youngs Modulus": 0.07},
}

# Calculator Functions
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
    mat = Material_detailes[inputs["Material"]]
    Max_stress = Max_strain * mat["youngs Modulus"]
    Min_stress = Min_strain * mat["youngs Modulus"]
    Mean_stress = (Max_stress + Min_stress) / 2
    Amp_stress = (Max_stress - Min_stress) / 2
    Mean_corr = Amp_stress / (1 - (Mean_stress / Amp_stress))
    Damage = Mean_corr ** mat["Fatigue constant"]
    cycles = (inputs["Target Damage"] * inputs["Factor of Safety"]) / Damage
    return {"Total Number of cycles": cycles}

# Test Definitions
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
                "type": "text",
                "value": "0.00054",
                "placeholder": "Enter: 0.00054"
            },
            "Calibration constant": {
                "type": "text",
                "value": "-1.356",
                "placeholder": "Enter: -1.356"
            },
            "Material": {"type": "selectbox", "options": list(Material_detailes.keys())},
            "Factor of Safety": {"type": "number", "value": 1.0},
        },
        "calculator": Front_Fork_Fatigue_calculation
    }
}

# Excel export
def create_excel_report(test_name, inputs, results):
    output = BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active

    # Header
    ws.merge_cells("A1:B1")
    ws["A1"] = "TEST SPECIFICATION CALCULATION REPORT"
    ws["A1"].font = Font(bold=True)
    ws.merge_cells("A2:B2")
    ws["A2"] = f"Test Type: {test_name}"

    row = 4
    for p, v in inputs.items():
        ws[f"A{row}"] = p
        ws[f"B{row}"] = f"{v:.8f}" if isinstance(v, float) else str(v)
        row += 1

    row += 1
    for p, v in results.items():
        ws[f"A{row}"] = p
        ws[f"B{row}"] = f"{v:.8f}" if isinstance(v, float) else str(v)
        row += 1

    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 20
    wb.save(output)
    return output.getvalue()

# PDF export
def create_pdf_report(test_name, inputs, results):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("TEST SPECIFICATION CALCULATION REPORT", styles['Title']))
    story.append(Paragraph(f"Test Type: {test_name}", styles['Normal']))
    story.append(Spacer(1,12))

    story.append(Paragraph("Input Parameters:", styles['Heading2']))
    for p, v in inputs.items():
        val = f"{v:.8f}" if isinstance(v, float) else str(v)
        story.append(Paragraph(f"{p}: {val}", styles['Normal']))

    story.append(Spacer(1,12))
    story.append(Paragraph("Results:", styles['Heading2']))
    for p, v in results.items():
        val = f"{v:.8f}" if isinstance(v, float) else str(v)
        story.append(Paragraph(f"{p}: {val}", styles['Normal']))

    doc.build(story)
    return buffer.getvalue()

# Streamlit UI
st.set_page_config(page_title="Test Spec Calculator", layout="wide")
st.title("Automated Test Specification Calculator")

selected_test = st.selectbox("Select Test Type", list(test_definitions.keys()))
test_config = test_definitions[selected_test]

col1, col2 = st.columns([2,1])
with col1:
    st.subheader("Input Parameters")
    inputs = {}
    for label, cfg in test_config["inputs"].items():
        key = f"{selected_test}_{label}"
        if cfg["type"] == "number":
            inputs[label] = st.number_input(label, key=key, **{k:v for k,v in cfg.items() if k!="type"})
        elif cfg["type"] == "selectbox":
            inputs[label] = st.selectbox(label, cfg["options"], key=key)
        elif cfg["type"] == "text":
            text_val = st.text_input(label, cfg.get("value",""), placeholder=cfg.get("placeholder",""), key=key)
            try:
                inputs[label] = float(text_val) if text_val else 0.0
            except ValueError:
                st.error(f"Please enter a valid number for {label}")
                inputs[label] = 0.0
    calculate = st.button("Calculate")

with col2:
    st.subheader("Results & Export")
    if calculate:
        try:
            result = test_config["calculator"](inputs)
            st.session_state["last"] = {"test":selected_test, "in":inputs, "res":result}
            st.success("Calculation Complete!")
            for k,v in result.items():
                st.metric(k, f"{v:.8f}" if isinstance(v,float) else str(v))
        except Exception as e:
            st.error(f"Error: {e}")

if "last" in st.session_state:
    st.markdown("---")
    data = st.session_state["last"]
    c1, c2 = st.columns(2)
    with c1:
        excel_data = create_excel_report(data["test"], data["in"], data["res"])
        st.download_button("Download Excel", data=excel_data,
            file_name=f"{data['test']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2:
        pdf_data = create_pdf_report(data["test"], data["in"], data["res"])
        st.download_button("Download PDF", data=pdf_data,
            file_name=f"{data['test']}.pdf",
            mime="application/pdf")

st.markdown("© 2025")  
