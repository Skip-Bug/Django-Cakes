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
            Edit: false,
            Name: 'Ирина',
            Phone: '8 909 000-00-00',
            Email: 'nyam@gmail.com',
            Schema: {
                name_format: (value) => {
                    const regex = /^[a-zA-Zа-яА-Я]+$/;
                    if (!value) return '⚠ Поле не может быть пустым';
                    if (!regex.test(value)) return '⚠ Недопустимые символы в имени';
                    return true;
                },
                phone_format: (value) => {
                    const regex = /^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$/;
                    if (!value) return '⚠ Поле не может быть пустым';
                    if (!regex.test(value)) return '⚠ Формат телефона нарушен';
                    return true;
                },
                email_format: (value) => {
                    const regex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i;
                    if (!value) return '⚠ Поле не может быть пустым';
                    if (!regex.test(value)) return '⚠ Формат почты нарушен';
                    return true;
                },
            },
        };
    },
    methods: {
        ApplyChanges() {
            this.Edit = false;
            this.$refs.HiddenFormSubmit.click();
        },
        async Logout() {
            await fetch('/auth/logout/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
            });
            window.location.href = '/';
        },
    },
}).mount('#LK');