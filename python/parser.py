import xml.etree.ElementTree as ET

# =====================================================
# Configuration
# =====================================================

# ARXML_FILE = "ConnectionEditor.arxml"
ARXML_FILE = "ECUExtract.arxml"
OUTPUT_M_FILE = "generate_model.m"

# =====================================================
# Helper Functions
# =====================================================

def tag_name(element):
    """
    Remove XML namespace.

    Example:
    {http://autosar.org/schema/r4.0}SHORT-NAME

    becomes:

    SHORT-NAME
    """
    return element.tag.split("}")[-1]


def get_short_name(element):
    """
    Return child SHORT-NAME value.
    """
    for child in element:
        if tag_name(child) == "SHORT-NAME":
            return child.text
    return None


# =====================================================
# Parse ARXML
# =====================================================

tree = ET.parse(ARXML_FILE)
root = tree.getroot()

print("Root Tag:", root.tag)

components = []
rports = []
pports = []
irvs = []
runnables = []

# =====================================================
# Discover Components
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
# Discover R Ports
# =====================================================

for elem in root.iter():

    if tag_name(elem) == "R-PORT-PROTOTYPE":

        name = get_short_name(elem)

        if name:
            rports.append(name)

# =====================================================
# Discover P Ports
# =====================================================

for elem in root.iter():

    if tag_name(elem) == "P-PORT-PROTOTYPE":

        name = get_short_name(elem)

        if name:
            pports.append(name)

# =====================================================
# Discover IRVs
# =====================================================

for elem in root.iter():

    if tag_name(elem) == "VARIABLE-DATA-PROTOTYPE":

        name = get_short_name(elem)

        if name:
            irvs.append(name)

# =====================================================
# Discover Runnables
# =====================================================

for elem in root.iter():

    if tag_name(elem) == "RUNNABLE-ENTITY":

        name = get_short_name(elem)

        if name:
            runnables.append(name)

# =====================================================
# Debug Output
# =====================================================

print("\nComponents")
print(components)

print("\nR Ports")
print(rports)

print("\nP Ports")
print(pports)

print("\nIRVs")
print(irvs)

print("\nRunnables")
print(runnables)

# =====================================================
# Determine Model Name
# =====================================================

if components:
    model_name = components[0]
else:
    model_name = "StubModel"

# =====================================================
# Generate MATLAB Script
# =====================================================

with open(OUTPUT_M_FILE, "w") as f:

    f.write("clc;\n")
    f.write("bdclose('all');\n\n")

    f.write(f"modelName = '{model_name}';\n\n")

    f.write("new_system(modelName);\n")
    f.write("open_system(modelName);\n\n")

    # =================================================
    # R Ports
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
    # P Ports
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
    # Runnables
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
    # Dummy Logic
    # =================================================

    f.write("%% DUMMY LOGIC\n")

    f.write(
        "add_block('simulink/Math Operations/Gain', ...\n"
        "    [modelName '/DummyLogic'], ...\n"
        "    'Gain','1', ...\n"
        "    'Position',[330 100 420 130]);\n\n"
    )

    # =================================================
    # Wiring
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
    # Build Settings
    # =================================================

    f.write("%% BUILD CONFIGURATION\n")

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

    f.write("save_system(modelName);\n")
    f.write("disp('Model Generated Successfully');\n")

print(f"\nGenerated file: {OUTPUT_M_FILE}")

