import streamlit as st

Material_detailes = {
    "Steel": {"Fatigue constant": 3, "youngs Modulus": 0.205},
    "Aluminum": {"Fatigue constant": 5, "youngs Modulus": 0.07},
}


# Define Your Test Config/Data Structure
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
        "calculator": "panic_brake_calculation"
    },
    "Front Fork Fatigue": {
        "inputs": {
            "Target Damage": {"type":"number","value":640582108680.192},
            "fork Length (mm)" : {"type":"number","value":545},
            "Max Load (kgf)" : {"type":"number","value":200},
            "Min Load (kgf)" : {"type":"number","value":-200},
            "Calibration factor" : {"type": "number","value": 0.0068,"min_value": 0.0001,"max_value": 0.01,"step": 0.0001,"format": "%.5f"},
            "Calibration constant" : {"type":"number","value":-1.356, "step":0.001, "format":"%.5f"},
            "Material" : {"type": "selectbox","options": list(Material_detailes.keys())},
            "Factor of Safety" :{"type":"number","value":1.0}
        },
        "calculator": "Front_Fork_Fatigue_calculation"
    }
}

#Calculator Function for Each Test

def panic_brake_calculation(inputs):
    force = inputs["Mass of the Vehicle (kg)"] * inputs["Max Deceleration (m/s^2)"]
    torque = force * inputs["Tyre rolling radius (m)"]
    applied_force = (torque / inputs["Fixture arm length (m)"]) / 9.81
    total_cycles = inputs["Total life (km)"] / inputs["Road to rig factor"]
    return {"Required Load (kg)": applied_force, "Required Cycles": total_cycles}

def Front_Fork_Fatigue_calculation(inputs):
    Max_BM = inputs["fork Length (mm)"]*inputs["Max Load (kgf)"]
    Min_BM = inputs["fork Length (mm)"]*inputs["Min Load (kgf)"]
    Max_strain = (Max_BM * inputs["Calibration factor"]) + inputs["Calibration constant"]
    Min_strain = (Min_BM * inputs["Calibration factor"]) + inputs["Calibration constant"]
    Material_type = inputs["Material"]
    Material_data = Material_detailes[Material_type]
    Max_stress = Max_strain * Material_data["youngs Modulus"]
    Min_stress = Min_strain * Material_data["youngs Modulus"]
    Mean_stress = (Max_stress + Min_stress)/2
    Amplitude_stress = (Max_stress - Min_stress)/2
    Mean_corrected_stress = Amplitude_stress/(1-(Mean_stress/Amplitude_stress))
    Damage_per_cycle = Mean_corrected_stress**Material_data["Fatigue constant"]
    Number_of_Cycles = (inputs["Target Damage"]*inputs["Factor of Safety"])/Damage_per_cycle
    
    return {"Total Number of cycles": Number_of_Cycles}

#Build the Streamlit UI Dynamically


# Dictionary and Calc Functions Defined Above

st.title("Automated Test Spec Calculation Tool")

# Select test
selected_test = st.selectbox("Select Test Type", list(test_definitions.keys()))

# Get selected test details
test_config = test_definitions[selected_test]
inputs = {}

# Show relevant input fields dynamically
st.subheader(f"Input Parameters for: {selected_test}")
for label, config in test_config["inputs"].items():
    key = f"{selected_test}_{label}"
    if config["type"] == "number":
        inputs[label] = st.number_input(label, key=key, **{k: v for k, v in config.items() if k != "type"})
    elif config["type"] == "selectbox":
        inputs[label] = st.selectbox(label, config["options"], key=key)

# Perform calculation
if st.button("Calculate"):
    # Call right calculator
    result = globals()[test_config["calculator"]](inputs)
    st.subheader("Results")
    for k, v in result.items():
        st.write(f"{k}: {v}")
