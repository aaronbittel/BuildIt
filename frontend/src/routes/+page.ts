import type { ColumnType } from "$lib/types";
import type { PageLoad } from "./$types";

export const load: PageLoad = () => {
    const columns: ColumnType[] = [
        {
            key: 'backlog',
            title: 'Backlog',
            items: [
                'extract columns into a Component',
                'add more metadata to the tasks',
                'Order of item depends on drag position',
                'create a backend',
            ],
        },
        {
            key: 'in_progress',
            title: 'In Progress',
            items: [
                'add button for creating new tasks',
            ],
        },
        {
            key: 'done',
            title: 'Done',
            items: [],
        }
    ];

    return { columns };
}
