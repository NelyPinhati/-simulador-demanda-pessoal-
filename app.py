import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Simulador de Demanda de Pessoal - TI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título e descrição
st.title("🧑‍💻 Simulador de Demanda Futura de Pessoal - TI")
st.markdown("""
Este simulador permite estimar a demanda futura de pessoal na área de TI com base em diferentes cenários.
Ajuste os parâmetros no painel lateral e veja como a demanda de pessoal pode evoluir ao longo do tempo.
""")

# Painel lateral para entrada de parâmetros
st.sidebar.header("Parâmetros da Simulação")

# Número atual de funcionários
funcionarios_atuais = st.sidebar.number_input(
    "Número atual de funcionários na TI",
    min_value=1,
    max_value=1000,
    value=150,
    help="Quantidade atual de funcionários na área de TI"
)

# Horizonte de simulação
horizonte = st.sidebar.slider(
    "Horizonte de simulação (meses)",
    min_value=1,
    max_value=60,
    value=24,
    help="Por quantos meses você deseja simular a demanda futura"
)

# Tipo de crescimento
tipo_crescimento = st.sidebar.radio(
    "Tipo de crescimento",
    options=["Percentual", "Baseado em projetos"],
    index=0,
    help="Escolha como o crescimento será calculado"
)

if tipo_crescimento == "Percentual":
    # Taxa de crescimento mensal
    taxa_crescimento = st.sidebar.slider(
        "Taxa de crescimento mensal (%)",
        min_value=-5.0,
        max_value=10.0,
        value=1.0,
        step=0.1,
        help="Crescimento percentual mensal esperado na demanda de pessoal"
    ) / 100  # Convertendo para decimal
    
    # Variação sazonal
    usar_sazonalidade = st.sidebar.checkbox(
        "Incluir variação sazonal",
        value=False,
        help="Adiciona variação sazonal ao crescimento (ex: mais projetos em certos meses)"
    )
    
    if usar_sazonalidade:
        st.sidebar.markdown("#### Fatores Sazonais por Mês")
        st.sidebar.markdown("Ajuste os fatores para cada mês (1.0 = normal, >1.0 = maior demanda, <1.0 = menor demanda)")
        
        # Criar sliders para cada mês
        fatores_sazonais = {}
        for mes in ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]:
            # Valores padrão que simulam um padrão sazonal comum em TI
            valor_padrao = 1.0
            if mes in ["Jan", "Fev"]:  # Início do ano, menos projetos
                valor_padrao = 0.9
            elif mes in ["Mar", "Abr", "Mai"]:  # Crescimento no Q2
                valor_padrao = 1.1
            elif mes in ["Nov", "Dez"]:  # Final de ano, menos projetos novos
                valor_padrao = 0.8
                
            fatores_sazonais[mes] = st.sidebar.slider(
                mes,
                min_value=0.5,
                max_value=1.5,
                value=valor_padrao,
                step=0.05
            )
    else:
        fatores_sazonais = {mes: 1.0 for mes in ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]}

else:  # Baseado em projetos
    # Projetos atuais
    projetos_atuais = st.sidebar.number_input(
        "Número atual de projetos",
        min_value=1,
        max_value=100,
        value=10,
        help="Quantidade atual de projetos ativos"
    )
    
    # Crescimento de projetos
    crescimento_projetos = st.sidebar.slider(
        "Crescimento mensal de projetos",
        min_value=-2,
        max_value=5,
        value=1,
        help="Quantos projetos novos (ou encerrados se negativo) por mês em média"
    )
    
    # Funcionários por projeto
    func_por_projeto = st.sidebar.slider(
        "Funcionários médios por projeto",
        min_value=1,
        max_value=20,
        value=5,
        help="Quantos funcionários são necessários, em média, por projeto"
    )

# Taxa de turnover
taxa_turnover = st.sidebar.slider(
    "Taxa de turnover mensal (%)",
    min_value=0.0,
    max_value=10.0,
    value=2.0,
    step=0.1,
    help="Percentual de funcionários que deixam a empresa mensalmente"
) / 100  # Convertendo para decimal

# Tempo médio para contratar
tempo_contratacao = st.sidebar.slider(
    "Tempo médio para contratar (meses)",
    min_value=0.5,
    max_value=6.0,
    value=2.0,
    step=0.5,
    help="Quanto tempo leva, em média, para contratar um novo funcionário"
)

# Contratações planejadas
st.sidebar.markdown("#### Contratações Planejadas")
usar_contratacoes_planejadas = st.sidebar.checkbox(
    "Incluir contratações já planejadas",
    value=False
)

contratacoes_planejadas = {}
if usar_contratacoes_planejadas:
    # Obter data atual
    data_atual = datetime.now()
    
    # Criar campos para os próximos 6 meses
    for i in range(6):
        mes_futuro = data_atual + timedelta(days=30*i)
        nome_mes = mes_futuro.strftime("%b/%Y")
        
        contratacoes_planejadas[nome_mes] = st.sidebar.number_input(
            f"Contratações em {nome_mes}",
            min_value=0,
            max_value=50,
            value=0
        )

# Botão para executar a simulação
st.sidebar.markdown("---")
executar = st.sidebar.button("Executar Simulação", type="primary")

# Função para calcular a simulação
def simular_demanda():
    # Criar dataframe para armazenar resultados
    data_atual = datetime.now()
    datas = [data_atual + timedelta(days=30*i) for i in range(horizonte)]
    
    df = pd.DataFrame({
        'Data': datas,
        'Mês': [d.strftime("%b/%Y") for d in datas],
        'Mês_Num': [d.month for d in datas],
        'Funcionários': [funcionarios_atuais] + [0] * (horizonte - 1),
        'Saídas': [0] * horizonte,
        'Contratações': [0] * horizonte,
        'Demanda': [funcionarios_atuais] + [0] * (horizonte - 1)
    })
    
    # Mapear nomes dos meses para fatores sazonais
    meses_abrev = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    df['Fator_Sazonal'] = df['Mês_Num'].apply(lambda x: fatores_sazonais[meses_abrev[x-1]])
    
    # Adicionar contratações planejadas
    if usar_contratacoes_planejadas:
        for mes, qtd in contratacoes_planejadas.items():
            if qtd > 0:
                idx = df[df['Mês'] == mes].index
                if len(idx) > 0:
                    df.loc[idx, 'Contratações'] += qtd
    
    # Calcular a evolução mês a mês
    if tipo_crescimento == "Percentual":
        # Inicializar variáveis para controle de contratações em andamento
        contratacoes_em_andamento = []
        
        for i in range(1, horizonte):
            # Calcular saídas (turnover)
            saidas = round(df.loc[i-1, 'Funcionários'] * taxa_turnover)
            df.loc[i, 'Saídas'] = saidas
            
            # Calcular crescimento com fator sazonal
            crescimento_base = df.loc[i-1, 'Funcionários'] * taxa_crescimento
            crescimento_ajustado = crescimento_base * df.loc[i, 'Fator_Sazonal']
            
            # Calcular demanda ideal (considerando crescimento e saídas)
            demanda_ideal = df.loc[i-1, 'Funcionários'] + crescimento_ajustado
            df.loc[i, 'Demanda'] = round(demanda_ideal)
            
            # Processar contratações em andamento que chegam neste mês
            contratacoes_concluidas = 0
            novas_contratacoes_em_andamento = []
            
            for tempo_restante, qtd in contratacoes_em_andamento:
                if tempo_restante <= 1:
                    contratacoes_concluidas += qtd
                else:
                    novas_contratacoes_em_andamento.append((tempo_restante - 1, qtd))
            
            contratacoes_em_andamento = novas_contratacoes_em_andamento
            
            # Adicionar contratações planejadas que chegam neste mês
            contratacoes_concluidas += df.loc[i, 'Contratações']
            
            # Calcular déficit (quantos funcionários faltam para atingir a demanda)
            funcionarios_sem_novas_contratacoes = df.loc[i-1, 'Funcionários'] - saidas + contratacoes_concluidas
            deficit = max(0, df.loc[i, 'Demanda'] - funcionarios_sem_novas_contratacoes)
            
            # Iniciar novas contratações para cobrir o déficit
            if deficit > 0 and tempo_contratacao > 0:
                contratacoes_em_andamento.append((tempo_contratacao, deficit))
            
            # Atualizar número de funcionários
            df.loc[i, 'Funcionários'] = funcionarios_sem_novas_contratacoes
            
            # Registrar contratações concluídas neste mês
            df.loc[i, 'Contratações'] = contratacoes_concluidas
    
    else:  # Baseado em projetos
        # Calcular evolução de projetos
        projetos = [projetos_atuais]
        for i in range(1, horizonte):
            projetos.append(max(0, projetos[i-1] + crescimento_projetos))
        
        df['Projetos'] = projetos
        df['Demanda'] = df['Projetos'] * func_por_projeto
        
        # Inicializar variáveis para controle de contratações em andamento
        contratacoes_em_andamento = []
        
        for i in range(1, horizonte):
            # Calcular saídas (turnover)
            saidas = round(df.loc[i-1, 'Funcionários'] * taxa_turnover)
            df.loc[i, 'Saídas'] = saidas
            
            # Processar contratações em andamento que chegam neste mês
            contratacoes_concluidas = 0
            novas_contratacoes_em_andamento = []
            
            for tempo_restante, qtd in contratacoes_em_andamento:
                if tempo_restante <= 1:
                    contratacoes_concluidas += qtd
                else:
                    novas_contratacoes_em_andamento.append((tempo_restante - 1, qtd))
            
            contratacoes_em_andamento = novas_contratacoes_em_andamento
            
            # Adicionar contratações planejadas que chegam neste mês
            contratacoes_concluidas += df.loc[i, 'Contratações']
            
            # Calcular déficit (quantos funcionários faltam para atingir a demanda)
            funcionarios_sem_novas_contratacoes = df.loc[i-1, 'Funcionários'] - saidas + contratacoes_concluidas
            deficit = max(0, df.loc[i, 'Demanda'] - funcionarios_sem_novas_contratacoes)
            
            # Iniciar novas contratações para cobrir o déficit
            if deficit > 0 and tempo_contratacao > 0:
                contratacoes_em_andamento.append((tempo_contratacao, deficit))
            
            # Atualizar número de funcionários
            df.loc[i, 'Funcionários'] = funcionarios_sem_novas_contratacoes
            
            # Registrar contratações concluídas neste mês
            df.loc[i, 'Contratações'] = contratacoes_concluidas
    
    # Calcular métricas adicionais
    df['Déficit'] = df['Demanda'] - df['Funcionários']
    df['Taxa_Cobertura'] = (df['Funcionários'] / df['Demanda']).clip(0, 1)
    
    return df

# Executar simulação quando o botão for clicado
if executar:
    with st.spinner("Executando simulação..."):
        resultados = simular_demanda()
    
    # Exibir resultados
    st.markdown("## Resultados da Simulação")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Funcionários Iniciais", 
            f"{funcionarios_atuais}"
        )
    with col2:
        st.metric(
            "Funcionários ao Final", 
            f"{resultados['Funcionários'].iloc[-1]}", 
            delta=f"{resultados['Funcionários'].iloc[-1] - funcionarios_atuais}"
        )
    with col3:
        st.metric(
            "Demanda ao Final", 
            f"{resultados['Demanda'].iloc[-1]}", 
            delta=f"{resultados['Demanda'].iloc[-1] - funcionarios_atuais}"
        )
    with col4:
        deficit_final = resultados['Déficit'].iloc[-1]
        st.metric(
            "Déficit ao Final", 
            f"{deficit_final}", 
            delta=f"{-deficit_final}" if deficit_final > 0 else None,
            delta_color="inverse"
        )
    
    # Gráfico de evolução
    st.markdown("### Evolução da Demanda vs. Funcionários Disponíveis")
    
    fig = go.Figure()
    
    # Adicionar linha de demanda
    fig.add_trace(go.Scatter(
        x=resultados['Mês'],
        y=resultados['Demanda'],
        mode='lines+markers',
        name='Demanda Prevista',
        line=dict(color='#FF4B4B', width=3),
        marker=dict(size=8)
    ))
    
    # Adicionar linha de funcionários
    fig.add_trace(go.Scatter(
        x=resultados['Mês'],
        y=resultados['Funcionários'],
        mode='lines+markers',
        name='Funcionários Disponíveis',
        line=dict(color='#4B4BFF', width=3),
        marker=dict(size=8)
    ))
    
    # Adicionar área de déficit
    deficit_y = []
    for i in range(len(resultados)):
        if resultados['Déficit'].iloc[i] > 0:
            deficit_y.append(resultados['Funcionários'].iloc[i])
        else:
            deficit_y.append(None)
    
    fig.add_trace(go.Scatter(
        x=resultados['Mês'],
        y=resultados['Demanda'],
        mode='none',
        name='Área de Déficit',
        fill='tonexty',
        fillcolor='rgba(255, 0, 0, 0.2)',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=resultados['Mês'],
        y=deficit_y,
        mode='none',
        showlegend=False
    ))
    
    # Configurar layout
    fig.update_layout(
        title='Evolução da Demanda vs. Funcionários Disponíveis',
        xaxis_title='Mês',
        yaxis_title='Número de Funcionários',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de contratações e saídas
    st.markdown("### Contratações e Saídas Mensais")
    
    fig2 = go.Figure()
    
    # Adicionar barras de contratações
    fig2.add_trace(go.Bar(
        x=resultados['Mês'],
        y=resultados['Contratações'],
        name='Contratações',
        marker_color='#4CAF50'
    ))
    
    # Adicionar barras de saídas
    fig2.add_trace(go.Bar(
        x=resultados['Mês'],
        y=resultados['Saídas'],
        name='Saídas (Turnover)',
        marker_color='#FF5722'
    ))
    
    # Configurar layout
    fig2.update_layout(
        title='Contratações e Saídas Mensais',
        xaxis_title='Mês',
        yaxis_title='Número de Funcionários',
        barmode='group',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=400
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Tabela de dados
    st.markdown("### Dados Detalhados da Simulação")
    
    # Preparar tabela para exibição
    tabela_exibicao = resultados[['Mês', 'Funcionários', 'Demanda', 'Déficit', 'Contratações', 'Saídas']]
    tabela_exibicao = tabela_exibicao.rename(columns={
        'Mês': 'Mês/Ano',
        'Funcionários': 'Funcionários Disponíveis',
        'Demanda': 'Demanda Prevista',
        'Déficit': 'Déficit de Pessoal',
        'Contratações': 'Contratações Concluídas',
        'Saídas': 'Saídas (Turnover)'
    })
    
    # Exibir tabela com formatação condicional
    st.dataframe(
        tabela_exibicao.style.background_gradient(
            subset=['Déficit de Pessoal'], 
            cmap='Reds',
            vmin=0,
            vmax=tabela_exibicao['Déficit de Pessoal'].max() if tabela_exibicao['Déficit de Pessoal'].max() > 0 else 1
        ),
        use_container_width=True
    )
    
    # Insights e recomendações
    st.markdown("## Insights e Recomendações")
    
    # Calcular métricas para insights
    deficit_maximo = resultados['Déficit'].max()
    mes_deficit_maximo = resultados.loc[resultados['Déficit'].idxmax(), 'Mês']
    meses_com_deficit = resultados[resultados['Déficit'] > 0].shape[0]
    percentual_meses_com_deficit = (meses_com_deficit / horizonte) * 100
    
    # Gerar insights baseados nos resultados
    insights = []
    
    if deficit_maximo > 0:
        insights.append(f"📊 **Déficit Máximo:** A simulação prevê um déficit máximo de {deficit_maximo} funcionários em {mes_deficit_maximo}.")
    
    if percentual_meses_com_deficit > 0:
        insights.append(f"⏱️ **Período de Déficit:** Em {percentual_meses_com_deficit:.1f}% dos meses simulados ({meses_com_deficit} de {horizonte}), a equipe estará abaixo da demanda prevista.")
    
    if tempo_contratacao > 1:
        insights.append(f"⚠️ **Tempo de Contratação:** O tempo médio de contratação de {tempo_contratacao} meses significa que você precisa iniciar o processo de recrutamento com antecedência para evitar déficits.")
    
    if taxa_turnover > 0.02:  # 2% ao mês é considerado alto
        insights.append(f"🚪 **Turnover Elevado:** A taxa de turnover de {taxa_turnover*100:.1f}% ao mês é significativa e pode estar impactando a capacidade de manter a equipe adequada.")
    
    # Exibir insights
    for insight in insights:
        st.markdown(insight)
    
    # Recomendações
    st.markdown("### Recomendações")
    
    recomendacoes = []
    
    if deficit_maximo > 10:
        recomendacoes.append("🔴 **Ação Urgente:** O déficit projetado é muito alto. Considere iniciar um programa de contratação acelerada ou rever a distribuição de projetos.")
    elif deficit_maximo > 5:
        recomendacoes.append("🟠 **Atenção:** O déficit projetado é significativo. Planeje contratações adicionais ou considere terceirização para períodos de pico.")
    elif deficit_maximo > 0:
        recomendacoes.append("🟡 **Monitoramento:** Há um pequeno déficit projetado. Monitore a situação e prepare-se para contratar conforme necessário.")
    else:
        recomendacoes.append("🟢 **Equipe Adequada:** A simulação não prevê déficit de pessoal no período analisado.")
    
    if tempo_contratacao > 2:
        recomendacoes.append("⏱️ **Processo de Contratação:** Considere otimizar o processo de recrutamento para reduzir o tempo médio de contratação.")
    
    if taxa_turnover > 0.03:  # 3% ao mês
        recomendacoes.append("🚪 **Retenção de Talentos:** Implemente estratégias para reduzir o turnover, como programas de desenvolvimento, ajustes salariais ou melhorias no ambiente de trabalho.")
    
    # Exibir recomendações
    for recomendacao in recomendacoes:
        st.markdown(recomendacao)
    
    # Exportar dados
    st.markdown("### Exportar Resultados")
    
    csv = resultados.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar dados da simulação (CSV)",
        data=csv,
        file_name=f"simulacao_demanda_pessoal_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

else:
    # Mensagem inicial quando a aplicação é carregada
    st.info("👈 Ajuste os parâmetros no painel lateral e clique em 'Executar Simulação' para ver os resultados.")
    
    # Explicação sobre o simulador
    st.markdown("""
    ## Como usar este simulador
    
    Este simulador de demanda de pessoal permite que você:
    
    1. **Defina cenários:** Ajuste parâmetros como taxa de crescimento, turnover e tempo de contratação.
    2. **Visualize tendências:** Veja gráficos da evolução da demanda vs. disponibilidade de pessoal.
    3. **Identifique déficits:** Descubra quando e onde podem ocorrer faltas de pessoal.
    4. **Planeje contratações:** Determine quando iniciar processos de recrutamento.
    
    ### Parâmetros importantes
    
    - **Taxa de crescimento:** Quanto a demanda aumenta mensalmente (%).
    - **Taxa de turnover:** Percentual de funcionários que deixam a empresa por mês.
    - **Tempo de contratação:** Quantos meses leva para contratar um novo funcionário.
    - **Contratações planejadas:** Contratações já aprovadas para os próximos meses.
    
    ### Interpretando os resultados
    
    - **Déficit de pessoal:** Diferença entre a demanda prevista e os funcionários disponíveis.
    - **Taxa de cobertura:** Percentual da demanda que está sendo atendida pela equipe atual.
    - **Insights e recomendações:** Sugestões baseadas nos resultados da simulação.
    """)
