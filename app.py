import streamlit as st
import pandas as pd
import math

# ----------------------------
# Config & constants
# ----------------------------
st.set_page_config(page_title="Duct Size Calculator", page_icon="📏", layout="centered")

DUCT_SIZES = [250, 225, 200, 180, 160, 125, 110, 88.9, 53.9]
DUCT_SPECS = {250: 237, 225: 213, 200: 188, 180: 169, 160: 150,
              125: 118, 110: 102 , 88.9: 82, 53.9: 50}

# ----------------------------
# Helper functions
# ----------------------------
def compute_fill_factor(total_qty: int) -> float | None:
    if total_qty <= 0: return None
    if total_qty == 1: return 0.53
    if total_qty == 2: return 0.31
    return 0.40

def circle_area(d_mm: float) -> float:
    return math.pi * (d_mm / 2.0) ** 2

def required_id_mm(total_cable_area_mm2: float, fill_factor: float) -> float:
    required_area = total_cable_area_mm2 / fill_factor
    return 2.0 * math.sqrt(required_area / math.pi)

def pick_recommended(required_id):
    for od in sorted(DUCT_SIZES):
        if DUCT_SPECS[od] >= required_id:
            return od
    return None

# ----------------------------
# Load Cable Data
# ----------------------------
try:
    df_cable_data = pd.read_csv("hf://datasets/Areeb41/Cable/Cable_Data.csv")
except:
    df_cable_data = pd.DataFrame()
    st.warning("Cable_Data not found. 'Select from list' will not work.")

# ----------------------------
# UI
# ----------------------------
st.title("Duct Size Calculator")
st.caption("Type Cable OD manually or select from available cables.")

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame([{"Cable OD (mm)": 1.0, "Qty": 1, "Cable TYPE": "", "Cable Name": "", "Cable Size": ""}])

if "delete_index" not in st.session_state:
    st.session_state.delete_index = None


updated_rows = []
for i, row in st.session_state.df.iterrows():
    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        od_option = st.radio(
            f"Cable {i+1} OD Input",
            ["Manual", "Select from list"],
            key=f"od_option_{i}",
            horizontal=True
        )

        if od_option == "Manual":
            od_val = st.text_input(
                f"Cable {i+1} OD (mm)",
                value=str(row.get("Cable OD (mm)", 0)),
                key=f"od_{i}"
            )
            try:
                od_val = float(od_val)
            except:
                od_val = 0.0
            type_sel = cable_sel = size_sel = ""

        else:
            if not df_cable_data.empty:
                # Level 1 - TYPE
                types_list = [""] + (df_cable_data["TYPE"].dropna().unique())
                try:
                    type_index = types_list.index(row.get("Cable TYPE", ""))
                except:
                    type_index = 0
                type_sel = st.selectbox(f"Type (Cable {i+1})", options=types_list, index=type_index, key=f"type_{i}")
                df_type = df_cable_data[df_cable_data["TYPE"] == type_sel] if type_sel else pd.DataFrame()

                # Level 2 - Cable
                cable_list = [""] + (df_type["Cable"].dropna().unique()) if not df_type.empty else [""]
                try:
                    cable_index = cable_list.index(row.get("Cable Name", ""))
                except:
                    cable_index = 0
                cable_sel = st.selectbox(f"Cable (Cable {i+1})", options=cable_list, index=cable_index, key=f"cable_{i}")
                df_cable = df_type[df_type["Cable"] == cable_sel] if cable_sel else pd.DataFrame()

                # Level 3 - Cable Size
                size_list = [""] + (df_cable["Cable Size mm2"].dropna().unique()) if not df_cable.empty else [""]
                try:
                    size_index = size_list.index(row.get("Cable Size", ""))
                except:
                    size_index = 0
                size_sel = st.selectbox(f"Size (Cable {i+1})", options=size_list, index=size_index, key=f"size_{i}")
                df_final = df_cable[df_cable["Cable Size mm2"] == size_sel] if size_sel else pd.DataFrame()

                # Get OD
                od_val = df_final["Cable Outer Diameter mm"].values[0] if not df_final.empty else 0.0
            else:
                type_sel = cable_sel = size_sel = ""
                od_val = 0.0

    # with col2:
    #     qty = st.slider(f"Qty {i+1}", 1, 20, int(row.get("Qty",1)), key=f"qty_{i}")
        
    with col2:
        qty_str = st.text_input(
            f"Qty {i+1}",
            value=str(int(row.get("Qty", 1))),
            key=f"qty_{i}"
        )

        try:
            qty = int(qty_str)
            if qty < 1:
                qty = 1
        except ValueError:
            st.error("Please enter a valid integer")
            qty = 1    

    # with col3:
    #     # if st.button(f"❌ Delete {i+1}", key=f"del_{i}"):
    #     #     continue
    #     if st.button(f"❌ Delete {i+1}", key=f"del_{i}"):
    #         st.session_state.df = st.session_state.df.drop(index=i).reset_index(drop=True)
    #         st.rerun()


    updated_rows.append({
        "Cable OD (mm)": od_val,
        "Qty": qty,
        "Cable TYPE": type_sel,
        "Cable Name": cable_sel,
        "Cable Size": size_sel
    })

# st.session_state.df = pd.DataFrame(updated_rows)

DF_COLUMNS = ["Cable OD (mm)", "Qty", "Cable TYPE", "Cable Name", "Cable Size"]
st.session_state.df = pd.DataFrame(updated_rows, columns=DF_COLUMNS)

if not st.session_state.df.empty:
    if st.button(f"❌ Delete row"):
        st.session_state.df = st.session_state.df.iloc[:-1].reset_index(drop=True)
        st.rerun()

if st.button("➕ Add Row", key="add_row_btn"):
    df = st.session_state.df.copy()
    df.loc[len(df)] = {"Cable OD (mm)": 0, "Qty": 1, "Cable TYPE": "", "Cable Name": "", "Cable Size": ""}
    st.session_state.df = df
    st.rerun()

# ----------------------------
# Fill factor override
# ----------------------------
override_fill = st.checkbox("Override auto fill factor (%)")
custom_fill = st.slider("Fill factor (%)", 5, 90, 40) if override_fill else None

# ----------------------------
# Calculations
# ----------------------------
# df = st.session_state.df.copy()
# df = df[(df["Cable OD (mm)"] > 0) & (df["Qty"] > 0)]

df = st.session_state.df.copy()

required_cols = {"Cable OD (mm)", "Qty"}
if not required_cols.issubset(df.columns):
    df = pd.DataFrame(columns=["Cable OD (mm)", "Qty"])
else:
    df = df[(df["Cable OD (mm)"] > 0) & (df["Qty"] > 0)]





total_qty = int(df["Qty"].sum()) if not df.empty else 0
total_cable_area = float(
    (circle_area(df["Cable OD (mm)"]) * df["Qty"]).sum()
) if not df.empty else 0.0

fill_factor = (custom_fill / 100.0) if (override_fill and custom_fill) else compute_fill_factor(total_qty)

st.markdown("<div class='box'>", unsafe_allow_html=True)
st.subheader("Results")

left, mid, right = st.columns(3)
left.metric("Total cables", f"{total_qty}")
mid.metric("Total cable area", f"{total_cable_area:,.2f} mm²")
fill_display = f"{fill_factor*100:.0f}%" if fill_factor else "—"
right.metric("Fill factor used", fill_display)

if total_qty <= 0:
    st.info("Add at least one cable...")
else:
    req_id = required_id_mm(total_cable_area, fill_factor)
    recommended_od = pick_recommended(req_id)
    actual_fill_pct = (
        (total_cable_area / circle_area(DUCT_SPECS[recommended_od])) * 100.0
        if recommended_od else None
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Required Internal Diameter", f"{req_id:.2f} mm")
    # m2.metric("Required Outer Ø", "N/A")
    m2.metric("Recommended Duct Size", f"{recommended_od} mm" if recommended_od else "Not Available")

    if recommended_od is None:
        st.error("Duct Size not available")
    else:
        st.success(
            f"Recommended duct: **{recommended_od} mm** → "
            f"ID = {DUCT_SPECS[recommended_od]} mm | "
            f"Fill = {actual_fill_pct:.1f}%"
        )

    table = []
    for od in sorted(DUCT_SIZES):
        id_mm = DUCT_SPECS[od]
        fill_pct = (total_cable_area / circle_area(id_mm)) * 100
        table.append({
            "Duct OD (mm)": od,
            "Duct ID (mm)": id_mm,
            "Fill (%)": round(fill_pct, 1)
        })

    st.write("### Available Ducts Overview")
    st.dataframe(pd.DataFrame(table), use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
