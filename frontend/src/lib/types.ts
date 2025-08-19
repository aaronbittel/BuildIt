type TaskResponse = {
    id: number,
    name: string,
    stage_id: number,
    position: number,
};

type StageResponse = {
    id: number,
    name: string,
    tasks: TaskResponse[],
};

export type { TaskResponse, StageResponse }
