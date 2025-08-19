import type { StageResponse, TaskResponse } from "$lib/types"

const BACKEND_PREFIX = "http://localhost:8000"

async function updateTaskMoveRequest(
    taskID: number,
    stageID: number,
    toIndex: number,
): Promise<StageResponse[]> {
    const body = { to_index: toIndex, stage_id: stageID }
    const res = await fetch(`${BACKEND_PREFIX}/tasks/${taskID}/move`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });

    if (!res.ok) {
        const errDetail = await res.text();
        throw new Error(`Failed to update task: ${errDetail}`);
    }

    return await res.json();
}

async function updateTaskNameRequest(
    task_id: number,
    name: string
): Promise<TaskResponse> {
    const res = await fetch(`${BACKEND_PREFIX}/tasks/${task_id}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: name })
    });

    if (!res.ok) {
        const errDetail = await res.text();
        throw new Error(`Failed to update task: ${errDetail}`);
    }

    return await res.json();
}


async function addTaskRequest(
    stageID: number,
    taskName: string
): Promise<TaskResponse | undefined> {
    try {
        const res = await fetch(`${BACKEND_PREFIX}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stage_id: stageID,
                name: taskName
            })
        });

        if (!res.ok) {
            console.error('Failed to create task');
            return undefined;
        }

        const newTask: TaskResponse = await res.json();
        return newTask;
    } catch (err) {
        console.error('Error creating task', err);
        return undefined;
    }
}

async function resetDB() {
    const res = await fetch(`${BACKEND_PREFIX}/reset`, { method: 'POST' });
    if (!res.ok) {
        console.error('error resetting db');
        return;
    }
    return await res.json();
}

export { updateTaskMoveRequest, updateTaskNameRequest, addTaskRequest, resetDB }
