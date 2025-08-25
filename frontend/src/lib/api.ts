import type { StageResponse, TaskResponse } from '$lib/types';

const BACKEND_PREFIX = 'http://localhost:8000';

async function updateTaskMoveRequest(
	taskID: number,
	stageID: number,
	toIndex: number
): Promise<StageResponse[]> {
	const body = { to_index: toIndex, stage_id: stageID };
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

async function updateTaskNameRequest(task_id: number, name: string): Promise<TaskResponse> {
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
		return await res.json();
	} catch (err) {
		console.error('Error creating task', err);
		return undefined;
	}
}

async function resetDBRequest() {
	let res = await fetch(`${BACKEND_PREFIX}/reset`, { method: 'POST' });
	if (!res.ok) {
		console.error('error resetting db');
		return;
	}

	res = await fetch(`${BACKEND_PREFIX}/stages/tasks`);
	if (!res.ok) {
		console.error('error fetching stage details');
		return;
	}

	return await res.json();
}

async function deleteTaskRequest(task_id: number): Promise<boolean> {
	let res = await fetch(`${BACKEND_PREFIX}/tasks/${task_id}`, { method: 'DELETE' });
	if (!res.ok) {
		console.error('error deleting task with id', task_id);
		return false;
	}
	return true;
}

async function loadSnapshotRequest(name: string): Promise<boolean> {
	try {
		const response = await fetch(`${BACKEND_PREFIX}/dev/snapshots/load`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ name: name })
		});

		if (!response.ok) {
			console.error('error loading snapshot');
			return false;
		}
	} catch (err) {
		console.error('network error');
		return false;
	}

	return true;
}

export {
	BACKEND_PREFIX,
	updateTaskMoveRequest,
	updateTaskNameRequest,
	addTaskRequest,
	resetDBRequest,
	deleteTaskRequest,
	loadSnapshotRequest
};
