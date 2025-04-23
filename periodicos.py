import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import uuid
from datetime import datetime
import json
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Gerenciador de Empresas - Kanban",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Classes de dados
class Subtask:
    def __init__(self, employee_name: str, completed: bool = False):
        self.id = str(uuid.uuid4())
        self.employee_name = employee_name
        self.completed = completed

class CompanyTask:
    def __init__(self, company_name: str, cnpj: str, stage: str = "A CONTATAR", subtasks: list = None):
        self.id = str(uuid.uuid4())
        self.company_name = company_name
        self.cnpj = cnpj
        self.stage = stage
        self.subtasks = subtasks if subtasks else []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

# Funções de persistência
DATA_FILE = Path("company_tasks.json")

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [CompanyTask(**task) for task in data]
    return []

def save_data(tasks):
    data = [task.__dict__ for task in tasks]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, default=str, ensure_ascii=False)

# Inicialização do estado
def init_session_state():
    if 'company_tasks' not in st.session_state:
        st.session_state.company_tasks = load_data()
    if 'new_subtask_employee' not in st.session_state:
        st.session_state.new_subtask_employee = ""
    if 'new_task' not in st.session_state:
        st.session_state.new_task = {
            "company_name": "",
            "cnpj": "",
            "stage": "A CONTATAR",
            "subtasks": []
        }

# Funções auxiliares
def add_company_task():
    if not st.session_state.new_task["company_name"].strip() or not st.session_state.new_task["cnpj"].strip():
        st.error("Nome da empresa e CNPJ são obrigatórios!")
        return

    new_task = CompanyTask(
        company_name=st.session_state.new_task["company_name"],
        cnpj=st.session_state.new_task["cnpj"],
        stage=st.session_state.new_task["stage"],
        subtasks=[Subtask(sub["employee_name"]) for sub in st.session_state.new_task["subtasks"]]
    )
    
    st.session_state.company_tasks.append(new_task)
    save_data(st.session_state.company_tasks)
    
    st.session_state.new_task = {
        "company_name": "",
        "cnpj": "",
        "stage": "A CONTATAR",
        "subtasks": []
    }
    st.success("Empresa cadastrada com sucesso!")

def add_subtask():
    if not st.session_state.new_subtask_employee.strip():
        st.warning("Nome do funcionário é obrigatório!")
        return

    st.session_state.new_task["subtasks"].append({
        "employee_name": st.session_state.new_subtask_employee
    })
    st.session_state.new_subtask_employee = ""

def move_task(task_id: str, new_stage: str):
    for task in st.session_state.company_tasks:
        if task.id == task_id:
            task.stage = new_stage
            task.updated_at = datetime.now()
            break
    save_data(st.session_state.company_tasks)

def toggle_subtask_completion(task_id: str, subtask_id: str):
    for task in st.session_state.company_tasks:
        if task.id == task_id:
            for subtask in task.subtasks:
                if subtask.id == subtask_id:
                    subtask.completed = not subtask.completed
                    break
            break
    save_data(st.session_state.company_tasks)

def delete_task(task_id: str):
    st.session_state.company_tasks = [task for task in st.session_state.company_tasks if task.id != task_id]
    save_data(st.session_state.company_tasks)

# Interface Kanban
def render_kanban():
    stages = {
        "A CONTATAR": "📞",
        "CONTATANDO": "💬",
        "REPASSADO AGENDAMENTO": "📅",
        "CONCLUIDO": "✅"
    }
    
    cols = st.columns(len(stages))
    
    for i, (stage_name, emoji) in enumerate(stages.items()):
        with cols[i]:
            st.subheader(f"{emoji} {stage_name}")
            st.markdown("---")
            
            stage_tasks = [task for task in st.session_state.company_tasks if task.stage == stage_name]
            
            for task in stage_tasks:
                with st.container():
                    # Card da empresa
                    st.markdown(f"""
                    <div style="
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 12px;
                        margin-bottom: 10px;
                        background-color: #f9f9f9;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #333;">{task.company_name}</h4>
                            <button onclick="deleteTask('{task.id}')" style="
                                background: none;
                                border: none;
                                color: #ff4444;
                                cursor: pointer;
                                font-size: 16px;
                            ">🗑️</button>
                        </div>
                        <p style="margin: 5px 0; font-size: 12px; color: #666;">CNPJ: {task.cnpj}</p>
                        <p style="margin: 5px 0; font-size: 10px; color: #999;">
                            Atualizado em: {task.updated_at.strftime('%d/%m/%Y %H:%M')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Subtarefas (funcionários)
                    if task.subtasks:
                        with st.expander(f"👥 Funcionários ({len(task.subtasks)})", expanded=False):
                            for subtask in task.subtasks:
                                cols_sub = st.columns([1, 8, 1])
                                with cols_sub[0]:
                                    st.checkbox(
                                        "",
                                        value=subtask.completed,
                                        on_change=toggle_subtask_completion,
                                        args=(task.id, subtask.id),
                                        key=f"sub_{subtask.id}"
                                    )
                                with cols_sub[1]:
                                    st.markdown(
                                        f"<div style='{'text-decoration: line-through; color: gray' if subtask.completed else ''}'>{subtask.employee_name}</div>",
                                        unsafe_allow_html=True
                                    )
                    
                    # Botões de movimento
                    current_index = list(stages.keys()).index(task.stage)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if current_index > 0:
                            prev_stage = list(stages.keys())[current_index - 1]
                            if st.button("⬅️ Anterior", key=f"prev_{task.id}"):
                                move_task(task.id, prev_stage)
                                st.experimental_rerun()
                    
                    with col2:
                        if current_index < len(stages) - 1:
                            next_stage = list(stages.keys())[current_index + 1]
                            if st.button("Próximo ➡️", key=f"next_{task.id}"):
                                move_task(task.id, next_stage)
                                st.experimental_rerun()
                    
                    st.markdown("---")

# Formulário externo
def external_form():
    with st.expander("📝 Cadastrar Nova Empresa", expanded=True):
        st.write("Preencha os dados da empresa e seus funcionários:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(
                "Nome da Empresa*",
                key="new_task.company_name",
                value=st.session_state.new_task["company_name"],
                on_change=lambda: st.session_state.new_task.update({"company_name": st.session_state["new_task.company_name"]})
            )
        
        with col2:
            st.text_input(
                "CNPJ*",
                key="new_task.cnpj",
                value=st.session_state.new_task["cnpj"],
                on_change=lambda: st.session_state.new_task.update({"cnpj": st.session_state["new_task.cnpj"]})
            )
        
        st.selectbox(
            "Estágio Inicial",
            options=["A CONTATAR", "CONTATANDO", "REPASSADO AGENDAMENTO", "CONCLUIDO"],
            key="new_task.stage",
            index=0,
            on_change=lambda: st.session_state.new_task.update({"stage": st.session_state["new_task.stage"]})
        )
        
        st.markdown("**Funcionários:**")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(
                "Nome do Funcionário",
                key="new_subtask_employee",
                value=st.session_state.new_subtask_employee,
                on_change=lambda: setattr(st.session_state, 'new_subtask_employee', st.session_state["new_subtask_employee"]),
                label_visibility="collapsed"
            )
        with col2:
            st.button(
                "Adicionar Funcionário",
                on_click=add_subtask,
                disabled=not st.session_state.new_subtask_employee.strip()
            )
        
        # Lista de funcionários adicionados
        if st.session_state.new_task["subtasks"]:
            for i, subtask in enumerate(st.session_state.new_task["subtasks"]):
                cols = st.columns([1, 8, 1])
                cols[1].write(f"- {subtask['employee_name']}")
                with cols[2]:
                    if st.button("❌", key=f"remove_sub_{i}"):
                        st.session_state.new_task["subtasks"].pop(i)
                        st.experimental_rerun()
        
        st.button(
            "Cadastrar Empresa",
            on_click=add_company_task,
            disabled=not (st.session_state.new_task["company_name"].strip() and st.session_state.new_task["cnpj"].strip()),
            type="primary"
        )

# JavaScript para deletar tarefas
def inject_js():
    js = """
    <script>
    function deleteTask(taskId) {
        fetch('/delete_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({task_id: taskId})
        }).then(() => window.location.reload());
    }
    </script>
    """
    st.components.v1.html(js, height=0)

# Página principal
def main():
    init_session_state()
    inject_js()
    
    st.title("📊 Gerenciador de Empresas - Kanban")
    st.markdown("---")
    
    # Formulário externo
    external_form()
    
    st.markdown("---")
    
    # Visualização Kanban
    render_kanban()

if __name__ == "__main__":
    main()
