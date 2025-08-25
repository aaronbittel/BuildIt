import type { StageResponse, TaskResponse } from './types';
import { getContext, onDestroy, setContext } from 'svelte';

import { INACTIVE } from './utils';

class Stages {
	stages = $state<StageResponse[]>([]);

	constructor(stages: StageResponse[]) {
		this.stages = stages;
		onDestroy(() => {});
	}

	addTempStage() {
		this.stages = [...this.stages, { id: INACTIVE, name: '', tasks: [] }];
	}

	updateStage(id: number, newStage: StageResponse) {
		this.stages = this.stages.map((stage) => (stage.id === id ? newStage : stage));
	}

	addTask(stageID: number, newTask: TaskResponse) {
		const index = this.getStageIndexByID(stageID);
		if (index === undefined) {
			console.error(`Stage with ID ${stageID} not found while adding new task`);
			return;
		}
		this.stages[index].tasks.push(newTask);
	}

	sync(stages: StageResponse[]) {
		this.stages = stages;
	}

	removeTask(stageID: number, taskID: number) {
		const index = this.getStageIndexByID(stageID);
		if (index === undefined) {
			console.error(`Stage with ID ${stageID} not found while removing task`);
			return;
		}
		this.stages[index].tasks = this.stages[index].tasks.filter((t) => t.id !== taskID);
	}

	updateStageName(id: number, newName: string) {
		this.stages = this.stages.map((stage) =>
			stage.id === id ? { ...stage, name: newName } : stage
		);
	}

	private getStageIndexByID(stageID: number): number | undefined {
		const index = this.stages.findIndex((s) => s.id === stageID);
		return index !== -1 ? index : undefined;
	}
}

const STAGES_KEY = Symbol('STATUS');

function setStagesState(stages: StageResponse[]) {
	return setContext(STAGES_KEY, new Stages(stages));
}

function getStagesState() {
	return getContext<ReturnType<typeof setStagesState>>(STAGES_KEY);
}

export { Stages, setStagesState, getStagesState };
