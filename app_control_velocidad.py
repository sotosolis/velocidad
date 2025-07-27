
import streamlit as st
import pandas as pd
from io import BytesIO
import base64
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title='Control de Velocidad Zelestra', layout='wide')
st.image("https://i.imgur.com/70HnUsv.png", width=200)  # Logo representativo

st.title("Aplicación de Control de Velocidad - Faena Aurora")
st.write("Sube el archivo Excel con los registros de velocidad según el formulario de control.")

uploaded_file = st.file_uploader("Selecciona archivo Excel", type="xlsx")

# Tiempos mínimos entre puntos
tiempos_minimos = {
    ("A", "B"): 10,
    ("B", "C"): 8,
    ("C", "D"): 12,
    ("D", "E"): 10,
    ("E", "D"): 10,
    ("D", "C"): 12,
    ("C", "B"): 8,
    ("B", "A"): 10,
}

def evaluar_datos(df):
    df['Fecha y Hora'] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora (Formato hh:mm)'])
    df = df.sort_values(by=['PPU (Placa Patente Unica)', 'Fecha y Hora'])

    resultados = []

    for ppu, grupo in df.groupby('PPU (Placa Patente Unica)'):
        grupo = grupo.sort_values(by='Fecha y Hora').reset_index(drop=True)
        for i in range(len(grupo) - 1):
            inicio = grupo.loc[i]
            fin = grupo.loc[i + 1]
            if (
                inicio['PPU (Placa Patente Unica)'] == fin['PPU (Placa Patente Unica)'] and
                inicio['Sentido del Tránsito'] == fin['Sentido del Tránsito'] and
                inicio['Fecha'] == fin['Fecha']
            ):
                trayecto = (inicio['Punto de control'], fin['Punto de control'])
                if trayecto in tiempos_minimos:
                    tiempo_real = (fin['Fecha y Hora'] - inicio['Fecha y Hora']).total_seconds() / 60
                    tiempo_minimo = tiempos_minimos[trayecto]
                    if tiempo_real < 0:
                        estado = "Registro erróneo"
                    elif tiempo_real >= tiempo_minimo:
                        estado = "Cumple"
                    else:
                        estado = "No cumple"
                    resultados.append({
                        'PPU': ppu,
                        'Inicio': trayecto[0],
                        'Fin': trayecto[1],
                        'Hora inicio': inicio['Fecha y Hora'].strftime('%H:%M'),
                        'Hora fin': fin['Fecha y Hora'].strftime('%H:%M'),
                        'Minutos reales': round(tiempo_real, 2),
                        'Mínimo requerido': tiempo_minimo,
                        'Resultado': estado,
                        'Fecha': inicio['Fecha']
                    })
                else:
                    resultados.append({
                        'PPU': ppu,
                        'Inicio': trayecto[0],
                        'Fin': trayecto[1],
                        'Hora inicio': inicio['Fecha y Hora'].strftime('%H:%M'),
                        'Hora fin': fin['Fecha y Hora'].strftime('%H:%M'),
                        'Minutos reales': '',
                        'Mínimo requerido': '',
                        'Resultado': 'Tramo no definido',
                        'Fecha': inicio['Fecha']
                    })

    return pd.DataFrame(resultados)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if all(x in df.columns for x in ['Fecha', 'Hora (Formato hh:mm)', 'Punto de control', 'Sentido del Tránsito', 'PPU (Placa Patente Unica)']):
        resultados = evaluar_datos(df)

        fechas = resultados['Fecha'].unique()
        fecha_inicio = st.date_input("Desde", value=pd.to_datetime(fechas.min()))
        fecha_fin = st.date_input("Hasta", value=pd.to_datetime(fechas.max()))

        resultados_filtrados = resultados[
            (pd.to_datetime(resultados['Fecha']) >= pd.to_datetime(fecha_inicio)) &
            (pd.to_datetime(resultados['Fecha']) <= pd.to_datetime(fecha_fin))
        ]

        def color_estado(val):
            color = 'background-color: '
            if val == "Cumple":
                return color + 'lightgreen'
            elif val == "No cumple":
                return color + 'salmon'
            elif val in ["Registro erróneo", "Tramo no definido"]:
                return color + 'khaki'
            else:
                return ''

        st.dataframe(resultados_filtrados.style.applymap(color_estado, subset=['Resultado']), use_container_width=True)

        def convert_df(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Resultados')
            processed_data = output.getvalue()
            return processed_data

        st.download_button("📥 Descargar Excel", data=convert_df(resultados_filtrados),
                           file_name='Reporte_Velocidad_Zelestra.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.warning("El archivo no contiene las columnas requeridas.")
