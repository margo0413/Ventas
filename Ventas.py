import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import secrets

# Configuración de la pagina
st.set_page_config(page_title="Análisis de Ventas", page_icon="📈", layout="wide")

# Conectamos y cargamos datos desde PostgreSQL

@st.cache_data
def load_data():
    # Configuración de conexión a PostgreSQL
    # Puedes usar variables de entorno para mayor seguridad
    secrets = st.secrets["connections"]["postgresql"]

    db_config = {
        'host': secrets["host"],
        'database': secrets["database"],
        'user': secrets["username"],
        'password': secrets["password"],
        'port': secrets["port"]
    }
#    db_config = {
#        'host': os.getenv('DB_HOST', 'localhost'),
#        'database': os.getenv('DB_NAME', 'db_ventas'),
#        'user': os.getenv('DB_USER', 'postgres'),
#        'password': os.getenv('DB_PASSWORD', 'Karla1520'),
#        'port': os.getenv('DB_PORT', '5432')
#    }
    
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(**db_config)
        
        # Cargar datos de ventas
        df_ventas = pd.read_sql_query("SELECT * FROM ventas", conn)
        
        # Cargar datos de forecast
        df_forecast = pd.read_sql_query("SELECT * FROM forecast", conn)
        
        conn.close()
        
        # Procesar datos (igual que antes)
        df_ventas['mes'] = pd.to_datetime(df_ventas['fecha']).dt.month
        df_ventas['valor_moneda_grupo'] = df_ventas['valor_moneda_grupo'] * -1
        
        return df_ventas, df_forecast

    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        return pd.DataFrame(), pd.DataFrame()
    
    
# Alternativa: Si prefieres usar SQLAlchemy (recomendado para producción)
#@st.cache_data
#def load_data_sqlalchemy():
#    from sqlalchemy import create_engine
#    import urllib.parse
    
#    secrets = st.secrets["connections"]["postgresql"]   
    # Configuración de conexión
#    db_user = secrets["username"]   
#    db_password = secrets["password"]
#    db_host = secrets["host"]
#    db_port = secrets["port"]
#    db_name = secrets["database"]

    #db_user = os.getenv('DB_USER', 'postgres')
    #db_password = urllib.parse.quote_plus(os.getenv('DB_PASSWORD', 'Karla1520'))
    #db_host = os.getenv('DB_HOST', 'localhost')
    #db_port = os.getenv('DB_PORT', '5432')
    #db_name = os.getenv('DB_NAME', 'tu_base_de_datos')
    
    # Crear connection string
#    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
#    try:
#        engine = create_engine(connection_string)
        
        # Cargar datos
#        df_ventas = pd.read_sql("SELECT * FROM ventas", engine)
#        df_forecast = pd.read_sql("SELECT * FROM forecast", engine)
        
        # Procesar datos
#        df_ventas['mes'] = pd.to_datetime(df_ventas['fecha']).dt.month
#        df_ventas['valor_moneda_grupo'] = df_ventas['valor_moneda_grupo'] * -1
        
#        return df_ventas, df_forecast
        
#    except Exception as e:
#        st.error(f"Error conectando a la base de datos: {e}")
#        return pd.DataFrame(), pd.DataFrame()



# Cargar datos (elige una de las dos funciones anteriores)
df_ventas, df_forecast = load_data()  # o load_data_sqlalchemy()

# Verificar si hay datos cargados
if df_ventas.empty or df_forecast.empty:
    st.error("No se pudieron cargar los datos. Verifica la conexión a la base de datos.")
    st.stop()

# Lista de los meses disponibles 
meses_disponibles = sorted(df_ventas['mes'].unique())
nombres_meses = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# Filtro por mes 
st.sidebar.header("Filtros")
mes_seleccionado = st.sidebar.selectbox(
    "Seleccionar Mes:",
    options=meses_disponibles,
    format_func=lambda x: nombres_meses[x]
)

# Aplicamos los filtros a los datos 
df_ventas_filtro = df_ventas[df_ventas['mes'] == mes_seleccionado]
df_forecast_filtro = df_forecast[df_forecast['mes'] == mes_seleccionado]

st.title(f"📊 Análisis de Ventas OMNIA - {nombres_meses[mes_seleccionado]}")

# Mostrar métricas clave en columnas
col1, col2, col3 = st.columns(3)

with col1:
    # Total Forecast
    total_forecast = df_forecast_filtro['Monto_euro'].sum()
    st.metric("Total Forecast", f"${total_forecast:,.0f}")  
with col2:
    # Total Ventas
    total_ventas = df_ventas_filtro['valor_moneda_grupo'].sum()
    st.metric("Total Ventas", f"${total_ventas:,.0f}")
with col3:
    # Porcentaje de Ventas vs Forecast
    if total_forecast > 0:
        porcent_ventas = (total_ventas / total_forecast) * 100
    else:
        porcent_ventas = 0  
    st.metric("Ventas vs Forecast (%)", f"{porcent_ventas:.0f}%")

# Tabla de ventas segmento
# Datos agrupados por segmento
ventas_segmento = df_ventas_filtro.groupby('segmento')['valor_moneda_grupo'].sum().reset_index()
forecast_segmento = df_forecast_filtro.groupby('segmento')['Monto_euro'].sum().reset_index()

# Creación de la tabla
tabla_segmento = pd.merge(ventas_segmento, forecast_segmento, on='segmento', how='outer').fillna(0)
tabla_segmento.columns = ['Segmento', 'Ventas', 'Forecast']

# Agregamos columnas de % Ventas y % Forecast 
tabla_segmento['% Ventas'] = (tabla_segmento['Ventas']/tabla_segmento['Forecast'].sum()*100).round(0).astype(str) + '%'
tabla_segmento['% Forecast'] = (tabla_segmento['Forecast']/tabla_segmento['Forecast'].sum()*100).round(0).astype(str) + '%'

# Agregamos columna de % Ventas vs Forecast 
tabla_segmento['% Ventas vs Forecast'] = (tabla_segmento['Ventas'] / tabla_segmento['Forecast'] * 100).round(0).astype(str) + '%'

st.dataframe(tabla_segmento.style.format({'Ventas': '${:,.0f}', 'Forecast': '${:,.0f}'}), use_container_width=True)

st.markdown("---")

# Grafica de ventas por vendedor
ventas_vendedor = df_ventas_filtro.groupby('vendedor')['valor_moneda_grupo'].sum().reset_index()
fig_barras = go.Figure()
fig_barras.add_trace(go.Bar(
    x=ventas_vendedor['vendedor'],
    y=ventas_vendedor['valor_moneda_grupo'],
    marker_color='rgb(150, 207, 190)',
))

# Tabla de ventas por vendedores
forecast_vendedor = df_forecast_filtro.groupby('vendedor')['Monto_euro'].sum().reset_index()

# Creación de la tabla 
tabla_vendedores = pd.merge(ventas_vendedor, forecast_vendedor, on='vendedor', how='outer').fillna(0)
tabla_vendedores.columns = ['Vendedor','Ventas', 'Forecast']

# Agregamos columna de %
tabla_vendedores['%'] = (tabla_vendedores['Ventas']/tabla_vendedores['Forecast']*100).round(0).astype(str) + '%'

# Ordenar la tabla de vendedores por monto de ventas descendente
tabla_vendedores = tabla_vendedores.sort_values(by='Ventas', ascending=False).reset_index(drop=True)

# Visualizacion de los datos de Vendedores
col1, col2 = st.columns(2)

with col1:
    # Tabla de vendedores 
    st.subheader("Ventas por vendedor")
    st.dataframe(tabla_vendedores.style.format({'Ventas':'${:,.0f}','Forecast': '${:,.0f}'}), use_container_width=True)
with col2:
    # Grafica de venta por vendedor 
    st.plotly_chart(fig_barras, use_container_width=True)

# Tabla de Forecast por facturar 
# Filtrar conceptos no facturados y seleccionar los 5 mayores montos
no_facturados = df_forecast_filtro[df_forecast_filtro['facturado'] == 'No']
top_no_facturados = no_facturados.sort_values(by='Monto_euro', ascending=False).head(5)
tabla_no_facturados = top_no_facturados[['vendedor','orden_venta', 'cliente', 'Monto_euro', 'segmento']]

st.subheader("Top 5 No Facturados")
st.dataframe(tabla_no_facturados.style.format({'Monto_euro': '${:,.0f}'}), use_container_width=True)