type TaskResponse = {
	id: number;
	name: string;
	stage_id: number;
	position: number;
};

type StageResponse = {
	id: number;
	name: string;
	tasks: TaskResponse[];
};

type SnapshotResponse = {
	name: string;
	comment: string;
};

export type { TaskResponse, StageResponse, SnapshotResponse };
