import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import os
import numpy as np
from datetime import date, datetime
import io

# --- OLETUSASETUKSET (SESSION STATE) ---
DEFAULT_SETTINGS = {
    'line_color': "#4a90e2",
    'bg_color': "#404040",
    'fig_color': "#2b2b2b",
    'font_color': "#ffffff",
    'show_drought': True,
    'show_releases': False,  
    'show_medals': False,
    'sprite_zoom': 0.25,
    'conn_color': "#aaaaaa",
    'conn_style': "-",
    'conn_alpha': 0.7,
    'pos1_x': -20, 'pos1_y': 65,
    'pos2_x': 20, 'pos2_y': -65,
    'pos3_x': -30, 'pos3_y': 25,
    'pos4_x': 20, 'pos4_y': -30,
    'date_format': "DD.MM.YYYY"  # <-- UUSI: Oletuspäivämäärämuoto
}

for k, v in DEFAULT_SETTINGS.items():
    if k not in st.session_state:
        st.session_state[k] = v

def reset_settings():
    for k, v in DEFAULT_SETTINGS.items():
        st.session_state[k] = v

# --- SIVUN ASETUKSET ---
st.set_page_config(page_title="Keeper Timeline Generator", layout="wide")

st.title("Pokémon Sleep - Keeper Timeline Generator")
st.write("Upload your Keeper Data CSV to generate your personal timeline!")

# --- OHJEET KÄYTTÄJILLE & KAHVINAPPI ---
with st.expander("Instructions & How to format your data"):
    st.markdown("""
    ### 1. Use the Template
    The easiest way to get started is to make a copy of this Google Sheets template:  
    [**Keeper Timeline Template (Google Sheets)**](https://docs.google.com/spreadsheets/d/1o2I2QjT5jY4hmJSGE9RHHfhpq5zuc3sJX3uQVp6PpZM/edit?usp=sharing)  
    *(Go to File -> Make a copy. Once you have filled in your data, go to File -> Download -> Comma Separated Values (.csv) and upload it below).*

    ### 2. Finding your stats in Pokémon Sleep
    To fill out the "Total Pokémon caught" field accurately, open Pokémon Sleep, tap on **Main Menu -> Profile**, and look for the **"Pokémon Befriended"** stat.

    ### 3. Column Explanations
    * **Days played:** This will fill itself when you add pokémon caught date. You don't have to fill this info manually.
    * **Keeper #:** Which keeper this is in chronological order (e.g., 1, 2, 3...).
    * **Pokémon:** The name of the Pokémon. **Important formatting rules:**
        * **Shinies:** Add an 'S' to the end of the name (e.g., `EspeonS`, `CharizardS`).
        * **Variants/Event Pokémon:** Write them together based on the event (e.g., `PikachuHoliday`, `PikachuHalloweenOrange`, `WooperPaldean`).
        * **Shiny Variants:** Combine both rules. (e.g., `PikachuHolidayS`).
    * **Ingredient:** *(Optional)* Type 'A' for Mono or 'B' for ABB. Leave empty if not applicable.
    * **[Your Start Date]:** Format exactly as DD.MM.YYYY (e.g., 17.08.2024). Row 1 determines your starting date, and other dates are the pokémon's caught date.
    * **Befriend #:** *(Optional)* How many of this specific species you had befriended before catching this keeper. If you leave this empty, the graph will just show a normal dot without a number.
    """)
    
    st.write("---")
    
    instr_col1, instr_col2 = st.columns([2, 1])
    
    with instr_col1:
        try:
            st.image("esimerkki.png", caption="Example of how your data should look in the spreadsheet.")
        except FileNotFoundError:
            st.warning("Example image not found. (Developer: Make sure 'esimerkki.png' is in the folder!)")
            
    with instr_col2:
        st.markdown("""
        If you enjoy this tool and want to support my coffee addiction:<br><br>
        <a href="https://buymeacoffee.com/kfgasd" target="_blank">
            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 50px !important;width: 181px !important;" >
        </a>
        """, unsafe_allow_html=True)

# --- KÄYTTÖLIITTYMÄ ---
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("1. Upload Keeper Data (CSV)", type="csv")

with col2:
    total_caught = st.number_input("2. Total Pokémon caught:", min_value=1, value=1000)

# --- GRAAFIN KUSTOMOINTI ---
with st.expander("🎨 Graph Customization (Colors & Layout)"):
    st.write("Customize the look of your timeline. If things get messy, you can always reset!")
    
    st.button("🔄 Reset to Defaults", on_click=reset_settings)
    
    # --- UUSI: Päivämäärämuodon valinta lisätty ensimmäiselle riville ---
    c_col1, c_col2, c_col3, c_col4, c_col5 = st.columns(5)
    line_color = c_col1.color_picker("Timeline & Dots", key='line_color')
    bg_color = c_col2.color_picker("Inner BG", key='bg_color')
    fig_color = c_col3.color_picker("Outer BG", key='fig_color')
    font_color = c_col4.color_picker("Font Color", key='font_color')
    date_format = c_col5.selectbox("Date Format", ["DD.MM.YYYY", "MM/DD/YYYY", "YYYY-MM-DD"], key='date_format')
    
    st.write("---")
    
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    show_drought = t_col1.checkbox("Highlight longest drought", key='show_drought')
    show_releases = t_col2.checkbox("Show Pokémon Releases", key='show_releases')
    show_medals = t_col3.checkbox("Show Befriend Medals", key='show_medals')
    sprite_zoom = t_col4.slider("Pokémon Sprite Size", min_value=0.05, max_value=1.0, step=0.05, key='sprite_zoom')
    
    st.write("---")
    
    st.write("Adjust Connector Lines (Nodes to Pokémon):")
    l_col1, l_col2, l_col3 = st.columns(3)
    conn_color = l_col1.color_picker("Line Color", key='conn_color')
    conn_style = l_col2.selectbox("Line Style", ["-", "--", "-.", ":"], index=0, key='conn_style')
    conn_alpha = l_col3.slider("Line Transparency (Alpha)", 0.1, 1.0, step=0.1, key='conn_alpha')
    
    st.write("---")
    
    st.write("Adjust Pokémon image positions (X, Y offsets from the point):")
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    pos1_x = p_col1.number_input("Pos 1 (X)", key='pos1_x')
    pos1_y = p_col1.number_input("Pos 1 (Y)", key='pos1_y')
    pos2_x = p_col2.number_input("Pos 2 (X)", key='pos2_x')
    pos2_y = p_col2.number_input("Pos 2 (Y)", key='pos2_y')
    pos3_x = p_col3.number_input("Pos 3 (X)", key='pos3_x')
    pos3_y = p_col3.number_input("Pos 3 (Y)", key='pos3_y')
    pos4_x = p_col4.number_input("Pos 4 (X)", key='pos4_x')
    pos4_y = p_col4.number_input("Pos 4 (Y)", key='pos4_y')

# --- JOS TIEDOSTO ON LADATTU, PIIRRETÄÄN GRAAFI ---
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    try:
        aloitus_str = df.columns[4]
        aloituspaiva = datetime.strptime(aloitus_str, '%d.%m.%Y').date()
    except Exception as e:
        aloituspaiva = date(2024, 8, 17)
        st.warning("Start date couldn't be read from cell E1. Using default.")

    tanaan = date.today()
    total_days = (tanaan - aloituspaiva).days
    total_keepers = len(df) 
    
    pokemon_julkaisut = {
        'Suicune': date(2024, 9, 2), 'Aggron': date(2024, 10, 2), 'Luxray': date(2024, 10, 2),
        'Vikavolt': date(2024, 10, 2), 'WooperPaldean': date(2024, 4, 29), 'Entei': date(2024, 5, 20),
        'Mr. Mime': date(2023, 9, 12), 'Clefable': date(2023, 9, 28), 'Banette': date(2023, 10, 24),
        'PikachuHalloweenOrange': date(2023, 10, 24), 'Steelix': date(2023, 11, 14), 
        'Delibird': date(2023, 12, 18), 'Abomasnow': date(2023, 12, 18), 'PikachuHoliday': date(2023, 12, 18),
        'Dragonite': date(2024, 1, 24), 'Ralts': date(2024, 1, 24), 'Bewear': date(2024, 1, 24),
        'Dedenne': date(2024, 3, 11), 'Raikou': date(2024, 3, 25), 'Comfey': date(2024, 4, 22),
        'Ninetales': date(2024, 5, 6), 'Cramorant': date(2024, 6, 17), 'Meowscarada': date(2024, 7, 15),
        'Skeledirge': date(2024, 7, 15), 'Quaquaval': date(2024, 7, 15), 'Quagsire': date(2024, 8, 19),
        'Drifblim': date(2024, 10, 11), 'Mimikyu': date(2024, 10, 28), 'PikachuHalloweenPurple': date(2024, 10, 28),
        'Weavile': date(2024, 12, 3), 'NinetalesAlolan': date(2024, 12, 23), 'Pawmot': date(2024, 12, 23),
        'EeveeHoliday': date(2024, 12, 23), 'Braviary': date(2025, 1, 20), 'Clodsire': date(2025, 2, 10),
        'Musharna': date(2025, 3, 17), 'Cresselia': date(2025, 3, 31), 'Darkrai': date(2025, 3, 31),
        'Blissey': date(2025, 5, 5), 'Mawile': date(2025, 6, 9), 'Farfetchd': date(2025, 6, 23),
        'Sceptile': date(2025, 7, 14), 'Blaziken': date(2025, 7, 14), 'Swampert': date(2025, 7, 14),
        'Plusle': date(2025, 7, 14), 'Minun': date(2025, 7, 14), 'Toxel': date(2025, 8, 11),
        'Xatu': date(2025, 9, 29), 'Gourgeist': date(2025, 10, 21), 'EeveeHalloween': date(2025, 10, 28),
        'Spiritomb': date(2025, 12, 1), 'Togedemaru': date(2025, 12, 22), 'Cetitan': date(2025, 12, 22),
        'SphealHoliday': date(2025, 12, 22), 'Shuckle': date(2026, 1, 19), 'Ribombee': date(2026, 2, 9),
        'Mew': date(2026, 2, 27), 'Noivern': date(2026, 3, 23), 'Latias': date(2026, 4, 6),
        'Sandslash': date(2026, 4, 27),
        'Tyrantrum': date(2026, 5, 11),
        'Drampa': date(2026, 5, 25),
        'Latios': date(2026, 6, 8),
    }

    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    ax.plot(df['Days played'], df['Keeper #'], color=line_color, linewidth=2, zorder=1)

    if show_drought:
        paivien_erotukset = df['Days played'].diff()
        longest_drought = paivien_erotukset.max()
        drought_loppu_index = paivien_erotukset.idxmax()
        drought_alku_index = drought_loppu_index - 1
        x_drought = [df['Days played'].iloc[drought_alku_index], df['Days played'].iloc[drought_loppu_index]]
        y_drought = [df['Keeper #'].iloc[drought_alku_index], df['Keeper #'].iloc[drought_loppu_index]]
        ax.plot(x_drought, y_drought, color='#FF4444', linewidth=3, zorder=2)
    else:
        longest_drought = df['Days played'].diff().max()

    keeper_percentage = (total_keepers / total_caught) * 100
    catches_per_day = total_caught / total_days
    days_per_keeper = total_days / total_keepers

    stats_text = (f"Days played: {total_days}\n"
                  f"Total caught: {total_caught}\n"
                  f"Keeper %: {keeper_percentage:.2f}%\n"
                  f"Catches/day: {catches_per_day:.2f}\n"
                  f"Days/keeper: {days_per_keeper:.1f} days\n"
                  f"Longest drought: {int(longest_drought)} days")

    props = dict(boxstyle='square,pad=1', facecolor='#555555', alpha=0.8, edgecolor='none')
    ax.text(0.03, 0.95, stats_text, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', color=font_color, bbox=props, zorder=3)

    def get_image(path, zoom_val):
        if os.path.exists(path):
            try:
                img_array = plt.imread(path)
                if len(img_array.shape) == 3 and img_array.shape[2] == 4: 
                    alpha = img_array[:, :, 3]
                    y_coords, x_coords = np.nonzero(alpha > 0) 
                    if len(y_coords) > 0 and len(x_coords) > 0:
                        ymin, ymax = np.min(y_coords), np.max(y_coords)
                        xmin, xmax = np.min(x_coords), np.max(x_coords)
                        img_array = img_array[ymin:ymax+1, xmin:xmax+1]
                return OffsetImage(img_array, zoom=zoom_val) 
            except Exception:
                return None
        return None

    for i, row in df.iterrows():
        x = row['Days played']
        y = row['Keeper #']
        pokemon_name = str(row['Pokémon']).strip()
        ingredient = row['Ingredient']
        
        node_color = line_color
        
        if show_medals and 'Befriend #' in df.columns and pd.notna(row.get('Befriend #')):
            try:
                befriend_count = int(float(row['Befriend #']))
                if befriend_count >= 100:
                    node_color = "#FFD700"  # Kulta
                elif befriend_count >= 40:
                    node_color = "#C0C0C0"  # Hopea
                elif befriend_count >= 10:
                    node_color = "#CD7F32"  # Pronssi
            except ValueError:
                pass 
        
        ax.scatter(x, y, color=node_color, s=150, zorder=2)
        
        if 'Befriend #' in df.columns and pd.notna(row.get('Befriend #')):
            try:
                befriend_numero = str(int(float(row['Befriend #'])))
                ax.text(x, y, befriend_numero, color='white', fontsize=8, fontweight='bold', 
                        ha='center', va='center', zorder=3)
            except ValueError:
                pass

        image_path = f"kuvat/{pokemon_name}.png"
        img = get_image(image_path, sprite_zoom)
        
        if img:
            if i % 4 == 0:
                xybox_offset = (pos1_x, pos1_y)   
            elif i % 4 == 1:
                xybox_offset = (pos2_x, pos2_y)   
            elif i % 4 == 2:
                xybox_offset = (pos3_x, pos3_y)   
            else:
                xybox_offset = (pos4_x, pos4_y)   

            ab = AnnotationBbox(
                img, xy=(x, y), xybox=xybox_offset, xycoords='data', boxcoords='offset points',     
                pad=0.0, frameon=False,
                arrowprops=dict(
                    arrowstyle="-", 
                    color=conn_color, 
                    linestyle=conn_style, 
                    linewidth=1.5, 
                    alpha=conn_alpha,
                    connectionstyle="arc3,rad=0.2", 
                    shrinkA=8, shrinkB=0
                )
            )
            ax.add_artist(ab)
            
            if pd.notna(ingredient):
                ing_str = str(ingredient).strip().upper()
                if ing_str in ['A', 'B']:
                    text_x_offset = xybox_offset[0] + 15
                    text_y_offset = xybox_offset[1] + 15
                    bg_color_badge = '#FFD700' if ing_str == 'A' else '#C0C0C0'
                    ax.annotate(ing_str, xy=(x, y), xytext=(text_x_offset, text_y_offset),
                                textcoords='offset points', color='black', fontsize=9,
                                fontweight='bold', ha='center', va='center',
                                bbox=dict(boxstyle='circle,pad=0.2', facecolor=bg_color_badge, edgecolor='#333333', linewidth=1, alpha=0.9),
                                zorder=4)

    ax.set_facecolor(bg_color)
    fig.patch.set_facecolor(fig_color)
    ax.tick_params(colors=font_color)
    ax.xaxis.label.set_color(font_color)
    ax.yaxis.label.set_color(font_color)
    ax.grid(color=font_color, alpha=0.2, linestyle='-', linewidth=1)
    
    ax.set_xlabel('Days played', fontsize=12, labelpad=10)
    ax.set_ylabel('Catch number', fontsize=12, labelpad=10)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    if show_releases:
        paivien_julkaisut = {}
        for poke, julkaisupaiva in pokemon_julkaisut.items():
            paivia_aloituksesta = (julkaisupaiva - aloituspaiva).days
            if 0 < paivia_aloituksesta <= total_days:
                if paivia_aloituksesta not in paivien_julkaisut:
                    paivien_julkaisut[paivia_aloituksesta] = []
                paivien_julkaisut[paivia_aloituksesta].append(poke)
        
        max_pino_korkeus = max([len(lista) for lista in paivien_julkaisut.values()]) if paivien_julkaisut else 0
        pohja_y = -40 - ((max_pino_korkeus - 1) * 35) if max_pino_korkeus > 0 else -40

        for paivia, poket in paivien_julkaisut.items():
            pino_koko = len(poket)
            
            for i, poke in enumerate(poket):
                y_offset = pohja_y + (i * 35)
                
                image_path = f"kuvat/{poke}.png"
                img = get_image(image_path, sprite_zoom)
                
                if img:
                    if i == pino_koko - 1:
                        arr_props = dict(arrowstyle="-", color=font_color, alpha=0.5, linestyle="--", linewidth=1.5, shrinkA=0, shrinkB=0)
                    else:
                        arr_props = None 
                        
                    ab = AnnotationBbox(
                        img, xy=(paivia, 0), xycoords=('data', 'axes fraction'),
                        xybox=(0, y_offset), boxcoords='offset points', pad=0.0, frameon=False,
                        arrowprops=arr_props
                    )
                    ab.set_clip_on(False) 
                    ax.add_artist(ab)

        teksti_y = pohja_y - 25
        ax.annotate("Pokémon Releases", xy=(0.5, 0), xycoords='axes fraction',  
                    xytext=(0, teksti_y), textcoords='offset points', color=font_color, alpha=0.7, 
                    fontsize=12, fontstyle='italic', ha='center', va='top', annotation_clip=False)
        
        dynaaminen_margin = 0.20 + (max_pino_korkeus * 0.05)
        plt.subplots_adjust(bottom=dynaaminen_margin)
        
    else:
        plt.subplots_adjust(bottom=0.15) 

    # --- UUSI: Päivämäärämuotoilun logiikka ---
    if date_format == "MM/DD/YYYY":
        fmt_str = "%m/%d/%Y"
    elif date_format == "YYYY-MM-DD":
        fmt_str = "%Y-%m-%d"
    else:
        fmt_str = "%d.%m.%Y" # Oletus (DD.MM.YYYY)

    ax.annotate(f"Started: {aloituspaiva.strftime(fmt_str)}", xy=(0, 0), xycoords='axes fraction',  
                xytext=(-115, -35), textcoords='offset points', color=font_color, alpha=0.7, fontsize=11, ha='left', va='top', annotation_clip=False)

    ax.annotate(f"Data as of: {tanaan.strftime(fmt_str)}", xy=(1, 1), xycoords='axes fraction',  
                xytext=(40, 10), textcoords='offset points', color=font_color, alpha=0.7, fontsize=11, ha='right', va='bottom', annotation_clip=False)

    # --- NÄYTETÄÄN GRAAFI STREAMLITISSÄ (Esikatselulaatu) ---
    st.pyplot(fig)

    st.write("---")
    
    # --- LATAUSNAPPI HUIKEALLA RESOLUUTIOLLA ---
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    
    st.download_button(
        label="Download High-Resolution Timeline",
        data=buf,
        file_name="my_keeper_timeline.png",
        mime="image/png",
        use_container_width=True 
    )