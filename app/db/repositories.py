from typing import Iterable

from app.db.database import get_conn


def create_project(project_id: str, name: str, path: str, now: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO projects(id,name,path,created_at,updated_at,last_indexed_at) VALUES (?,?,?,?,?,NULL)",
            (project_id, name, path, now, now),
        )


def get_project(project_id: str):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()


def list_chunks(project_id: str):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM chunks WHERE project_id=?", (project_id,)).fetchall()


def delete_project_chunks(project_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM chunks WHERE project_id=?", (project_id,))


def add_chunks(project_id: str, rows: Iterable[tuple]) -> int:
    count = 0
    with get_conn() as conn:
        for row in rows:
            conn.execute(
                "INSERT INTO chunks(project_id,file_path,chunk_index,start_line,end_line,text,embedding) VALUES (?,?,?,?,?,?,?)",
                (project_id, *row),
            )
            count += 1
    return count


def update_last_indexed(project_id: str, now: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE projects SET last_indexed_at=? WHERE id=?", (now, project_id))
