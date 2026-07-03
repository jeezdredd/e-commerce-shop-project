var mix = {
	methods: {
		signUp () {
			const name = document.querySelector('#name').value
			const username = document.querySelector('#login').value
			const password = document.querySelector('#password').value
			this.postData('/api/sign-up/', JSON.stringify({ name, username, password }))
				.then(() => {
					location.assign(`/`)
				})
				.catch((error) => {
					alert(error?.response?.data?.error ?? 'Ошибка регистрации')
				})
		}
	},
	mounted() {
	},
	data() {
		return {}
	}
}
