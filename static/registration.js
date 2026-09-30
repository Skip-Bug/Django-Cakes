function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

Vue.createApp({
    components: {
        VForm: VeeValidate.Form,
        VField: VeeValidate.Field,
        ErrorMessage: VeeValidate.ErrorMessage,
    },
    data() {
        return {
            RegSchema: {
                reg: (value) => (value ? true : 'Поле не заполнено'),
            },
            Step: 'Number',
            RegInput: '',
            EnteredNumber: '',
            ServerError: '',
            Sending: false,
        };
    },
    methods: {
        async RegSubmit() {
            this.ServerError = '';
            this.Sending = true;

            const url = this.Step === 'Number'
                ? '/auth/request-code/'
                : '/auth/verify-code/';

            const body = new FormData();
            if (this.Step === 'Number') {
                body.append('phone', this.RegInput);
            } else {
                body.append('phone', this.EnteredNumber);
                body.append('code', this.RegInput);
            }

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                    body,
                });
                const data = await response.json();

                if (!data.ok) {
                    this.ServerError = data.error || 'Произошла ошибка';
                    return;
                }

                if (this.Step === 'Number') {
                    this.EnteredNumber = this.RegInput;
                    this.Step = 'Code';
                    this.RegInput = '';
                } else {
                    this.RegInput = 'Регистрация успешна';
                    setTimeout(() => window.location.reload(), 800);
                }
            } catch (e) {
                this.ServerError = 'Ошибка сети';
            } finally {
                this.Sending = false;
            }
        },
        ToRegStep1() {
            this.Step = 'Number';
            this.RegInput = this.EnteredNumber;
            this.ServerError = '';
        },
        Reset() {
            this.Step = 'Number';
            this.RegInput = '';
            this.EnteredNumber = '';
            this.ServerError = '';
        },
    },
}).mount('#RegModal');