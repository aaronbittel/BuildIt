import type { StageResponse } from "$lib/types";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch }) => {
    const response = await fetch("http://localhost:8000/stages/tasks");
    const stages: StageResponse[] = await response.json();
    return { stages };
}
