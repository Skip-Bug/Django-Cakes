const app = Vue.createApp({
    name: "App",
    components: {
        VForm: VeeValidate.Form,
        VField: VeeValidate.Field,
        ErrorMessage: VeeValidate.ErrorMessage,
    },
    data() {
         
            const cakeData = JSON.parse(
                document.getElementById("cake-data").textContent
            );
            const orderErrors = JSON.parse(
                document.getElementById("order-errors").textContent
            );
            const prefill = JSON.parse(
                document.getElementById("order-prefill").textContent
            );
            const selected = {};
            cakeData.parts.forEach(part => {
                selected[part.id] = null;
            });

            return {

                schema2: {
                    name: (value) => {
                        if (value) {
                            return true;
                        }
                        return ' имя';
                    },
                    phone: (value) => {
                        if (value) {
                            return true;
                        }
                        return ' телефон';
                    },
                    name_format: (value) => {
                        const regex = /^[a-zA-Zа-яА-Я]+$/
                        if (!value) {
                            return true;
                        }
                        if ( !regex.test(value)) {

                            return '⚠ Формат имени нарушен';
                        }
                        return true;
                    },
                    email_format: (value) => {
                        const regex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i
                        if (!value) {
                            return true;
                        }
                        if ( !regex.test(value)) {

                            return '⚠ Формат почты нарушен';
                        }
                        return true;
                    },
                    phone_format:(value) => {
                        const regex = /^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$/
                        if (!value) {
                            return true;
                        }
                        if ( !regex.test(value)) {

                            return '⚠ Формат телефона нарушен';
                        }
                        return true;
                    },
                    email: (value) => {
                        if (value) {
                            return true;
                        }
                        return ' почту';
                    },
                    address: (value) => {
                        if (value) {
                            return true;
                        }
                        return ' адрес';
                    },
                    date: (value) => {
                        if (value) {
                            return true;
                        }
                        return ' дату доставки';
                    },
                    time: (value) => {
                        if (value) {
                            return true;
                        }
                        return ' время доставки';
                    }
                },
            basePrice: cakeData.base_price,
            OrderErrors: orderErrors,
            parts: cakeData.parts,
            selected: selected,

            Words: prefill.inscription || '',
            Comments: prefill.comment || '',
            Designed: false,

            Name: prefill.guest_name || '',
            Phone: prefill.guest_phone || null,
            Email: prefill.guest_email || null,
            Address: prefill.address || null,
            Dates: prefill.delivery_date || null,
            Time: prefill.delivery_time || null,
            DelivComments: prefill.delivery_comment || ''
        }
    },
    methods: {
        optionName(part, id) {
            const opt = part.options.find(o => o.id === id);
            return opt ? opt.name : '—';
        },
        ToPayment() {
            this.Designed = true
            setTimeout(() => this.$refs.ToPayment.click(), 0);
        }
    },
    computed: {
        schema1() {
            const schema = {};
            this.parts.forEach(part => {
                if (part.required) {
                    schema['part_' + part.id] = (value) => {
                        if (value) return true;
                        return 'Укажите: ' + part.name;
                    };
                }
            });
            return schema;
        },
        SelectedOptions() {
            const ids = [];

            this.parts.forEach(part => {
                if (part.requires_text) return;
                const selectedId = this.selected[part.id];
                if (selectedId) ids.push(selectedId);
            });

            if (this.Words) {
                const wordsPart = this.parts.find(p => p.requires_text);
                if (wordsPart && wordsPart.options.length) {
                    ids.push(wordsPart.options[0].id);
                }
            }

            return JSON.stringify(ids);
        },
        Cost() {
            let cost = this.basePrice;

            this.parts.forEach(part => {
                const selectedId = this.selected[part.id];
                if (!selectedId) return;

                const opt = part.options.find(o => o.id === selectedId);
                if (opt) cost += opt.price;
            });

            if (this.Words) {
                const wordsPart = this.parts.find(p => p.requires_text);
                if (wordsPart && wordsPart.options.length) {
                    cost += wordsPart.options[0].price;
                }
            }

            return cost;
        }
    }
    
})

app.config.compilerOptions.delimiters = ['[[', ']]']
app.mount('#VueApp')