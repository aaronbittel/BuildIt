const ALPHABET = Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i));
const EMPTY = ' ';
const INACTIVE = -1;

function computeCornerLabels(names: string[]): string[] {
	const upperNames = names.map((name) => name.toUpperCase());
	let letters: string[] = new Array(names.length).fill(EMPTY);
	const maxLength = Math.max(...names.map((name) => name.length));

	for (let i = 0; i < maxLength; i++) {
		for (const [index, name] of upperNames.entries()) {
			if (letters[index] !== EMPTY || name.length <= i) {
				continue;
			}
			const candidate = name[i];
			if (letters.includes(candidate)) {
				continue;
			}
			letters[index] = candidate;
		}
	}

	for (const [index, letter] of letters.entries()) {
		if (letter !== EMPTY) {
			continue;
		}

		const unusedLetters = ALPHABET.filter((char) => !letters.includes(char));

		if (unusedLetters.length > 0) {
			letters[index] = unusedLetters[0];
		}
	}
	return letters;
}

export { computeCornerLabels, INACTIVE };
