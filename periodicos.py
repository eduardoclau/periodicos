import streamlit as st
from typing import List, Dict, Optional
import uuid
from datetime import datetime

# Definindo tipos
class Subtask:
    def __init__(self, title: str, completed: bool = False):
        self.id = str(uuid.uuid4())
        self.title = title
        self.completed = completed

class Task:
    def __init__(self, title: str, description: str = "", subtasks: List[Subtask] = None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.completed = False
        self.subtasks = subtasks if subtasks else []
        self.created_at = datetime.now()

# Inicialização do estado da sessão
def init_session_state():
    if 'tasks' not in st.session_state:
        st.session_state.tasks = []
    if 'new_subtask_title' not in st.session_state:
        st.session_state.new_subtask_title = ""
    if 'new_task' not in st.session_state:
        st.session_state.new_task = {
            "title": "",
            "description": "",
            "subtasks": []
        }

# Funções auxiliares
def add_task():
    if not st.session_state.new_task["title"].strip():
        st.warning("O título da tarefa é obrigatório!")
        return

    new_task = Task(
        title=st.session_state.new_task["title"],
        description=st.session_state.new_task["description"],
        subtasks=[Subtask(sub["title"]) for sub in st.session_state.new_task["subtasks"]]
    )
    
    st.session_state.tasks.append(new_task)
    st.session_state.new_task = {
        "title": "",
        "description": "",
        "subtasks": []
    }
    st.success("Tarefa adicionada com sucesso!")

def add_subtask():
    if not st.session_state.new_subtask_title.strip():
        st.warning("O título da subtarefa é obrigatório!")
        return

    st.session_state.new_task["subtasks"].append({
        "title": st.session_state.new_subtask_title
    })
    st.session_state.new_subtask_title = ""

def toggle_task_completion(task_id: str):
    for task in st.session_state.tasks:
        if task.id == task_id:
            task.completed = not task.completed
            # Marcar todas as subtarefas como concluídas também
            for subtask in task.subtasks:
                subtask.completed = task.completed
            break

def toggle_subtask_completion(task_id: str, subtask_id: str):
    for task in st.session_state.tasks:
        if task.id == task_id:
            for subtask in task.subtasks:
                if subtask.id == subtask_id:
                    subtask.completed = not subtask.completed
                    # Verificar se todas as subtarefas estão concluídas
                    task.completed = all(sub.completed for sub in task.subtasks)
                    break
            break

def delete_task(task_id: str):
    st.session_state.tasks = [task for task in st.session_state.tasks if task.id != task_id]

def delete_subtask(task_id: str, subtask_id: str):
    for task in st.session_state.tasks:
        if task.id == task_id:
            task.subtasks = [sub for sub in task.subtasks if sub.id != subtask_id]
            # Atualizar status da tarefa principal
            task.completed = all(sub.completed for sub in task.subtasks)
            break

# Interface do usuário
def main():
    st.set_page_config(page_title="Gerenciador de Tarefas", page_icon="✅", layout="wide")
    init_session_state()

    st.title("📋 Gerenciador de Tarefas")
    st.markdown("---")

    # Seção para adicionar nova tarefa
    with st.expander("➕ Adicionar Nova Tarefa", expanded=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(
                "Título da Tarefa*",
                key="new_task.title",
                value=st.session_state.new_task["title"],
                on_change=lambda: st.session_state.new_task.update({"title": st.session_state["new_task.title"]})
            )
        with col2:
            st.text_input(
                "Nova Subtarefa",
                key="new_subtask_title",
                value=st.session_state.new_subtask_title,
                on_change=lambda: setattr(st.session_state, 'new_subtask_title', st.session_state["new_subtask_title"]),
                label_visibility="collapsed"
            )
        
        st.button(
            "Adicionar Subtarefa",
            on_click=add_subtask,
            disabled=not st.session_state.new_subtask_title.strip()
        )

        st.text_area(
            "Descrição (Opcional)",
            key="new_task.description",
            value=st.session_state.new_task["description"],
            on_change=lambda: st.session_state.new_task.update({"description": st.session_state["new_task.description"]})
        )

        # Lista de subtarefas adicionadas
        if st.session_state.new_task["subtasks"]:
            st.markdown("**Subtarefas:**")
            for i, subtask in enumerate(st.session_state.new_task["subtasks"]):
                cols = st.columns([1, 8, 1])
                cols[1].write(f"- {subtask['title']}")
                with cols[2]:
                    if st.button("❌", key=f"remove_sub_{i}"):
                        st.session_state.new_task["subtasks"].pop(i)
                        st.experimental_rerun()

        st.button(
            "Criar Tarefa",
            on_click=add_task,
            disabled=not st.session_state.new_task["title"].strip(),
            type="primary"
        )

    st.markdown("---")

    # Lista de tarefas existentes
    if not st.session_state.tasks:
        st.info("Nenhuma tarefa cadastrada ainda.")
    else:
        st.subheader("📌 Suas Tarefas")
        
        for task in st.session_state.tasks:
            with st.container():
                cols = st.columns([1, 8, 1])
                
                # Checkbox e título da tarefa
                with cols[0]:
                    st.checkbox(
                        "",
                        value=task.completed,
                        on_change=toggle_task_completion,
                        args=(task.id,),
                        key=f"task_{task.id}"
                    )
                
                with cols[1]:
                    st.markdown(
                        f"<h3 style='margin: 0; {'text-decoration: line-through; color: gray' if task.completed else ''}'>{task.title}</h3>",
                        unsafe_allow_html=True
                    )
                    if task.description:
                        st.markdown(
                            f"<div style='{'color: gray' if task.completed else ''}'>{task.description}</div>",
                            unsafe_allow_html=True
                        )
                
                # Botão de excluir
                with cols[2]:
                    if st.button("🗑️", key=f"del_{task.id}"):
                        delete_task(task.id)
                        st.experimental_rerun()
                
                # Subtarefas
                if task.subtasks:
                    with st.expander(f"📋 {len(task.subtasks)} subtarefa(s)", expanded=False):
                        for subtask in task.subtasks:
                            sub_cols = st.columns([1, 8, 1])
                            with sub_cols[0]:
                                st.checkbox(
                                    "",
                                    value=subtask.completed,
                                    on_change=toggle_subtask_completion,
                                    args=(task.id, subtask.id),
                                    key=f"sub_{subtask.id}"
                                )
                            with sub_cols[1]:
                                st.markdown(
                                    f"<div style='{'text-decoration: line-through; color: gray' if subtask.completed else ''}'>{subtask.title}</div>",
                                    unsafe_allow_html=True
                                )
                            with sub_cols[2]:
                                if st.button("🗑️", key=f"del_sub_{subtask.id}"):
                                    delete_subtask(task.id, subtask.id)
                                    st.experimental_rerun()
                
                st.markdown("---")

if __name__ == "__main__":
    main()
