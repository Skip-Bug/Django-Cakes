// Оформление заказа готовых тортов: выбор количества и подсчёт итога.
// Поля контактов и доставки — обычная Django-форма, здесь только список тортов.
const { createApp } = Vue;

createApp({
	data() {
		return {
			Cakes: window.READY_CAKES || [],
			Quantities: { ...(window.READY_SELECTED || {}) },
			MaxQty: window.READY_MAX_QTY || 20,
		};
	},
	computed: {
		CakesJson() {
			return JSON.stringify(
				Object.entries(this.Quantities)
					.filter(([, qty]) => qty > 0)
					.map(([id, qty]) => ({ id: Number(id), qty }))
			);
		},
		Cost() {
			return this.Cakes.reduce((sum, cake) => {
				const qty = this.Quantities[cake.id] || 0;
				return qty > 0 ? sum + cake.price * qty : sum;
			}, 0);
		},
	},
	methods: {
		Qty(id) {
			return this.Quantities[id] || 0;
		},
		SetQty(id, value) {
			const parsed = Number.parseInt(value, 10);
			if (Number.isNaN(parsed) || parsed <= 0) {
				delete this.Quantities[id];
				return;
			}
			this.Quantities[id] = Math.min(parsed, this.MaxQty);
		},
	},
	delimiters: ['[[', ']]'],
}).mount('#VueApp');