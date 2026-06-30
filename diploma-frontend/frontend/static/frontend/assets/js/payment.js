var mix = {
	methods: {
		submitPayment() {
			console.log('qweqwewqeqweqw')
			const orderId = location.pathname.startsWith('/payment/')
				? Number(location.pathname.replace('/payment/', '').replace('/', ''))
				: null
			this.postData(`/api/payment/${orderId}/`, {
				name: this.name,
				number: this.number,
				year: this.year,
				month: this.month,
				code: this.code
			})
				.then(() => {
					alert('Успешная оплата')
					this.number = ''
					this.name = ''
					this.year = ''
					this.month = ''
					this.code = ''
					location.assign('/')
				})
				.catch(() => {
					console.warn('Ошибка при оплате')
				})
		},
		generateAccount() {
			let n
			do {
				n = Math.floor(10000000 + Math.random() * 90000000)
			} while (n % 2 !== 0 || n % 10 === 0)
			const s = String(n)
			this.number = s.slice(0, 4) + ' ' + s.slice(4, 8)
		}
	},
	data() {
		return {
			number: '',
			month: '',
			year: '',
			name: '',
			code: ''
		}
	}
}