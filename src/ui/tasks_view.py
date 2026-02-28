import streamlit as st
from datetime import datetime

def render_tasks_section(db, client_id=None, can_id=None):
    """
    UI for managing tasks linked to a Client or specific CAN.
    """
    st.subheader("Task Management")

    # 1. Custom Task Creation
    with st.expander("Add New Task"):
        with st.form(f"new_task_form_{client_id or can_id}", clear_on_submit=True):
            desc = st.text_input("Task Description")
            due_date = st.date_input("Due Date")
            priority = st.selectbox("Priority", ["High", "Med", "Low"], index=1)
            if st.form_submit_button("Create Task"):
                if desc:
                    db.add_task(client_id=client_id, can_id=can_id, description=desc, 
                                due_date=due_date.strftime('%Y-%m-%d'), priority=priority)
                    st.success("Task created!")
                    st.rerun()
                else:
                    st.error("Task description is required.")

    # 2. Standardized MFD Workflows
    with st.expander("Schedule Standard MFD Task"):
        col1, col2 = st.columns([2, 1])
        with col1:
            task_type = st.selectbox("Standard Task Type", ["Annual Portfolio Review", "Quarterly KYC Update", "Nomination Review"])
        with col2:
            if st.button("Schedule Now", key=f"std_task_btn_{client_id or can_id}"):
                if task_type == "Annual Portfolio Review":
                    due = datetime.now().replace(year=datetime.now().year + 1)
                elif task_type == "Quarterly KYC Update":
                    month = (datetime.now().month + 2) % 12 + 1
                    year = datetime.now().year + (datetime.now().month + 2) // 12
                    due = datetime.now().replace(year=year, month=month)
                else:
                    due = datetime.now()
                
                db.add_task(client_id=client_id, can_id=can_id, description=task_type, 
                            due_date=due.strftime('%Y-%m-%d'), priority="Med")
                st.success(f"Scheduled: {task_type}!")
                st.rerun()

    # 3. Active Task List
    tasks_df = db.get_tasks(client_id=client_id, can_id=can_id)
    if not tasks_df.empty:
        for _, task in tasks_df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{task['description']}**")
                    st.caption(f"Due: {task['due_date']} | Priority: {task['priority']}")
                with col2:
                    new_status = st.selectbox("Status", ["Pending", "In Progress", "Completed", "Cancelled"], 
                                            index=["Pending", "In Progress", "Completed", "Cancelled"].index(task['status']),
                                            key=f"task_{task['id']}")
                    if new_status != task['status']:
                        db.update_task_status(task['id'], new_status)
                        st.rerun()
    else:
        st.info("No tasks for this investor.")
