import xml.etree.ElementTree as ET
from pathlib import Path

# =====================================================
# Configuration
# =====================================================

ARXML_FILE = "arxml/ECUExtract.arxml"

GENERATED_DIR = Path("generated")
GENERATED_DIR.mkdir(exist_ok=True)

OUTPUT_M_FILE = GENERATED_DIR / "generate_model.m"

# =====================================================
# Helper Functions
# =====================================================

def tag_name(element):
    """
    Remove XML namespace.

    Example:
    {http://autosar.org/schema/r4.0}SHORT-NAME

    becomes

    SHORT-NAME
    """
    return element.tag.split("}")[-1]


def get_short_name(element):
    """
    Return SHORT-NAME child text.
    """

    for child in element:
        if tag_name(child) == "SHORT-NAME":
            return child.text

    return None


# =====================================================
# Check ARXML Exists
# =====================================================

if not Path(ARXML_FILE).exists():
    raise FileNotFoundError(
        f"ARXML file not found: {ARXML_FILE}"
    )

# =====================================================
# Parse ARXML
# =====================================================

tree = ET.parse(ARXML_FILE)
root = tree.getroot()

print("=" * 50)
print("Root Tag :", root.tag)
print("=" * 50)

components = []
rports = []
pports = []
irvs = []
runnables = []

# =====================================================
# Component Discovery
# =====================================================

COMPONENT_TYPES = {
    "APPLICATION-SW-COMPONENT-TYPE",
    "COMPOSITION-SW-COMPONENT-TYPE",
    "SERVICE-SW-COMPONENT-TYPE",
    "COMPLEX-DEVICE-DRIVER-SW-COMPONENT-TYPE"
}

for elem in root.iter():

    tag = tag_name(elem)

    if tag in COMPONENT_TYPES:

        name = get_short_name(elem)

        if name:
            components.append(name)

# =====================================================
# R Ports
# =====================================================

for elem in root.iter():

    if tag_name(elem) == "R-PORT-PROTOTYPE":

        name = get_short_name(elem)

        if name:
            rports.append(name)

# =====================================================
# P Ports
# =====================================================

for elem in root.iter():

    if tag_name(elem) == "P-PORT-PROTOTYPE":

        name = get_short_name(elem)

        if name:
            pports.append(name)

# =====================================================
# IRVs
# =====================================================

for elem in root.iter():

    if tag_name(elem) == "VARIABLE-DATA-PROTOTYPE":

        name = get_short_name(elem)

        if name:
            irvs.append(name)

# =====================================================
# Runnables
# =====================================================

for elem in root.iter():

    if tag_name(elem) == "RUNNABLE-ENTITY":

        name = get_short_name(elem)

        if name:
            runnables.append(name)

# =====================================================
# Debug Output
# =====================================================

print("\nComponents:")
print(components)

print("\nR Ports:")
print(rports)

print("\nP Ports:")
print(pports)

print("\nIRVs:")
print(irvs)

print("\nRunnables:")
print(runnables)

# =====================================================
# Model Name
# =====================================================

if components:
    model_name = components[0]
else:
    model_name = "StubModel"

print(f"\nModel Name: {model_name}")

# =====================================================
# MATLAB Script Generation
# =====================================================

with open(OUTPUT_M_FILE, "w", encoding="utf-8") as f:

    f.write("clc;\n")
    f.write("bdclose('all');\n\n")

    f.write(f"modelName = '{model_name}';\n\n")

    f.write("new_system(modelName);\n")
    f.write("open_system(modelName);\n\n")

    # =================================================
    # R PORTS
    # =================================================

    f.write("%% R PORTS\n")

    y = 50

    for port in rports:

        f.write(
            f"add_block('simulink/Sources/In1', ...\n"
            f"    [modelName '/{port}'], ...\n"
            f"    'Position',[30 {y} 60 {y+20}]);\n\n"
        )

        y += 80

    # =================================================
    # P PORTS
    # =================================================

    f.write("%% P PORTS\n")

    y = 50

    for port in pports:

        f.write(
            f"add_block('simulink/Sinks/Out1', ...\n"
            f"    [modelName '/{port}'], ...\n"
            f"    'Position',[500 {y} 530 {y+20}]);\n\n"
        )

        y += 80

    # =================================================
    # IRVs
    # =================================================

    f.write("%% IRVs\n")

    y = 50

    for irv in irvs:

        f.write(
            f"add_block('simulink/Signal Routing/Data Store Memory', ...\n"
            f"    [modelName '/{irv}'], ...\n"
            f"    'Position',[220 {y} 330 {y+30}]);\n\n"
        )

        y += 80

    # =================================================
    # RUNNABLES
    # =================================================

    f.write("%% RUNNABLES\n")

    y = 220

    for runnable in runnables:

        f.write(
            f"add_block('simulink/Ports & Subsystems/Subsystem', ...\n"
            f"    [modelName '/{runnable}'], ...\n"
            f"    'Position',[150 {y} 280 {y+60}]);\n\n"
        )

        y += 120

    # =================================================
    # DUMMY LOGIC
    # =================================================

    f.write("%% DUMMY LOGIC\n")

    f.write(
        "add_block('simulink/Math Operations/Gain', ...\n"
        "    [modelName '/DummyLogic'], ...\n"
        "    'Gain','1', ...\n"
        "    'Position',[330 100 420 130]);\n\n"
    )

    # =================================================
    # CONNECTIONS
    # =================================================

    f.write("%% CONNECTIONS\n")

    if rports:

        f.write(
            f"add_line(modelName, ...\n"
            f"    '{rports[0]}/1', ...\n"
            f"    'DummyLogic/1');\n\n"
        )

    if pports:

        f.write(
            f"add_line(modelName, ...\n"
            f"    'DummyLogic/1', ...\n"
            f"    '{pports[0]}/1');\n\n"
        )

    # =================================================
    # MODEL CONFIGURATION
    # =================================================

    f.write("%% MODEL CONFIGURATION\n")

    f.write(
        "set_param(modelName, ...\n"
        "    'SolverType', ...\n"
        "    'Fixed-step');\n\n"
    )

    f.write(
        "set_param(modelName, ...\n"
        "    'Solver', ...\n"
        "    'FixedStepAuto');\n\n"
    )

    # =================================================
    # SAVE MODEL
    # =================================================

    f.write(
        "save_system(modelName, ..."
        " fullfile('generated',[modelName '.slx']));\n"
    )

    f.write("close_system(modelName);\n")

    f.write(
        "disp(['Generated: generated/' modelName '.slx']);\n"
    )

print("\n" + "=" * 50)
print(f"Generated MATLAB File: {OUTPUT_M_FILE}")
print("=" * 50)
