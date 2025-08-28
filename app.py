import streamlit as st
import pandas as pd
import math

# ----------------------------
# Config & constants
# ----------------------------
st.set_page_config(page_title="Duct Size Calculator", page_icon="📏", layout="centered")

# Your available duct sizes (mm)
DUCT_SIZES = [250, 225, 200, 180, 160, 125, 110, 60]


# st.markdown("""
# <style>
#   /* 🔒 Lock Streamlit in light theme */
#   :root {
#       background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
#       color: #111111;
#       font-family: 'Segoe UI', sans-serif;
#   }

#   body, .stApp {
#       color: var(--text-color) !important;
#       background: var(--background-color) !important;
#   }

#   /* Results section text */
#   div[data-testid="stMarkdownContainer"], 
#   div[data-testid="stMetricValue"], 
#   div[data-testid="stMetricDelta"] {
#       color: #111111 !important;
#       font-size: 1rem !important;
#       font-weight: 600 !important;
#   }

#   /* Results box */
#   .box {
#       background: #f5f5f5;  /* light gray background for contrast */
#       border: 1px solid #cccccc;
#       border-radius: 16px;
#       padding: 1rem 1.2rem;
#       color: #111111 !important;
#       font-weight: 600 !important;
#   }
# </style>
# """, unsafe_allow_html=True)



# ----------------------------
# Helpers
# ----------------------------
def compute_fill_factor(total_qty: int) -> float | None:
    if total_qty <= 0:
        return None
    if total_qty == 1:
        return 0.53  # 53%
    if total_qty == 2:
        return 0.31  # 31%
    return 0.40      # 40% for 3+

def circle_area(d_mm: float) -> float:
    """Area of a circle (mm²) from diameter in mm."""
    return math.pi * (d_mm / 2.0) ** 2

def required_id_mm(total_cable_area_mm2: float, fill_factor: float) -> float:
    """Required internal diameter (mm) given total cable area and fill factor."""
    required_area = total_cable_area_mm2 / fill_factor
    return 2.0 * math.sqrt(required_area / math.pi)

def pick_recommended(size_needed: float, available_sizes: list[float]) -> float | None:
    """Pick the smallest available size >= needed."""
    for s in sorted(available_sizes):
        if s >= size_needed:
            return s
    return None

# ----------------------------
# UI
# ----------------------------
st.title("📏 Duct Size Calculator")
st.caption("Applies NFPA 70 / NEC Chapter 9, Table 1 fill limits based on quantity of cables inside a duct.")

with st.container():
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    st.subheader("Cable List")
    st.write("Add your cable types (OD in mm) and quantities. Rows are editable and you can add/remove as needed.")

    # Initialize editable table
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame([{"Cable OD (mm)": 1.0, "Qty": 1}])

    updated_rows = []
    for i, row in st.session_state.df.iterrows():
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            od = st.text_input(
                f"Cable {i+1} OD (mm)",
                value=str(row["Cable OD (mm)"]),
                key=f"od_{i}"
            )
            try:
                od_val = float(od)
            except:
                od_val = 0.0

        with col2:
            qty = st.slider(
                f"Cable {i+1} Qty",
                min_value=1,
                max_value=20,
                value=int(row["Qty"]),
                key=f"qty_{i}"
            )

        with col3:
            if st.button(f"❌ Delete {i+1}", key=f"del_{i}"):
                continue  # skip adding this row (deletes it)

        updated_rows.append({"Cable OD (mm)": od_val, "Qty": qty})

    # Update dataframe
    st.session_state.df = pd.DataFrame(updated_rows)

    # Add new row button
    if st.button("➕ Add Row", key="add_row_btn"):
        df = st.session_state.df.copy()
        df.loc[len(df)] = {"Cable OD (mm)": 0.0, "Qty": 1}
        st.session_state.df = df
        st.rerun()



    with st.expander("Advanced options"):
        list_kind = st.radio(
            "Your available duct list represents:",
            ["Outer Diameter (OD)", "Inner Diameter (ID)"],
            index=0,
            horizontal=True
        )
        wall_thk = st.number_input(
            "Assumed duct wall thickness (mm) (used only if list = OD)",
            min_value=0.0, value=10.0, step=0.5
        )
        override_fill = st.checkbox("Override auto fill factor (%)")
        custom_fill = st.slider("Fill factor (%)", 5, 90, 40) if override_fill else None

    cols = st.columns([1,1,1])
    with cols[0]:
        if st.button("🧹 Reset table"):
            st.session_state.df = pd.DataFrame([{"Cable OD (mm)": 0, "Qty": 1}])

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------
# Calculations
# ----------------------------
df = st.session_state.df.copy()
# keep only valid rows
df = df[(df["Cable OD (mm)"] > 0) & (df["Qty"] > 0)]

total_qty = int(df["Qty"].sum()) if not df.empty else 0
total_cable_area = float((circle_area(df["Cable OD (mm)"]) * df["Qty"]).sum()) if not df.empty else 0.0

auto_fill = compute_fill_factor(total_qty)
fill_factor = (custom_fill / 100.0) if override_fill and custom_fill else auto_fill

st.markdown("<div class='box'>", unsafe_allow_html=True)
st.subheader("Results")

left, mid, right = st.columns(3)
left.metric("Total cables", f"{total_qty}")
mid.metric("Total cable area", f"{total_cable_area:,.2f} mm²")
fill_display = f"{fill_factor*100:.0f}%" if fill_factor else "—"
right.metric("Fill factor used", fill_display)

st.markdown(
    "<div class='small-note'>Per NFPA 70 / NEC Chapter 9, Table 1: "
    "1 cable → 53%, 2 cables → 31%, 3+ cables → 40%. "
    "You can override this in Advanced options.</div>",
    unsafe_allow_html=True
)

if total_qty <= 0:
    st.info("Add at least one cable row with a positive OD and quantity.")
else:
    if fill_factor is None or fill_factor <= 0:
        st.error("Invalid fill factor. Please adjust in Advanced options.")
    else:
        # Required internal diameter
        req_id = required_id_mm(total_cable_area, fill_factor)

        # If the list is OD, compute required OD; otherwise compare ID directly
        if list_kind == "Outer Diameter (OD)":
            req_od = req_id + 2.0 * wall_thk
            needed_for_compare = req_od
        else:
            req_od = None
            needed_for_compare = req_id

        # Pick recommended
        recommended = pick_recommended(needed_for_compare, DUCT_SIZES)

        # Compute actual fill if we use "recommended"
        def internal_d_from_listed(listed_size):
            if list_kind == "Outer Diameter (OD)":
                return max(listed_size - 2.0 * wall_thk, 0.0)
            return listed_size

        actual_fill_pct = None
        if recommended is not None:
            internal_d = internal_d_from_listed(recommended)
            if internal_d > 0:
                actual_fill_pct = (total_cable_area / circle_area(internal_d)) * 100.0

        # Show main metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Required Internal Ø", f"{req_id:.2f} mm")
        if req_od is not None:
            m2.metric("Required Outer Ø", f"{req_od:.2f} mm")
        else:
            m2.metric("Required Ø (list is ID)", f"{req_id:.2f} mm")
        if recommended is not None:
            m3.metric("Recommended size", f"{recommended} mm")
        else:
            m3.metric("Recommended size", "—")

        if recommended is None:
            st.error("No suitable size found in the provided list.")
        else:
            st.success(
                f"Recommended duct: **{recommended} mm** "
                f"({list_kind}). "
                + (f"Estimated actual fill: **{actual_fill_pct:.1f}%**." if actual_fill_pct is not None else "")
            )

        # Table of all available sizes & resulting fill
        table = []
        for s in sorted(DUCT_SIZES):
            id_mm = internal_d_from_listed(s)
            area_mm2 = circle_area(id_mm) if id_mm > 0 else float('nan')
            fill_pct = (total_cable_area / area_mm2 * 100.0) if area_mm2 and area_mm2 > 0 else float('nan')
            table.append({
                "Listed size (mm)": s,
                "Used as": list_kind,
                "Assumed ID (mm)": round(id_mm, 2),
                "Fill (%)": round(fill_pct, 1) if not math.isnan(fill_pct) else None
            })
        st.write("### Available sizes overview")
        st.dataframe(pd.DataFrame(table), use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    "<div class='small-note'>Note: Advanced Options If your catalog sizes are nominal Inner Diameter rather than Outer Diameter, switch the "
    "radio to `Inner Diameter (ID)`. If OD is used, adjust wall thickness to match your duct material/spec.</div>",
    unsafe_allow_html=True
)
