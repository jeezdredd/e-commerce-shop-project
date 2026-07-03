var mix = {
    computed: {
      tags () {
          if(!this.product?.tags) return []
          return this.product.tags
      }
    },
    methods: {
        changeCount (value) {
            this.count = this.count + value
            if (this.count < 1) this.count = 1
        },
        getProduct() {
            const productId = location.pathname.startsWith('/product/')
            ? Number(location.pathname.replace('/product/', '').replace('/', ''))
            : null
            this.getData(`/api/product/${productId}/`).then(data => {
                this.product = {
                    ...this.product,
                    ...data
                }
                if(data.images.length)
                    this.activePhoto = 0
            }).catch(() => {
                this.product = {}
                console.warn('Ошибка при получении товара')
            })
        },
        submitReview () {
            this.postData(`/api/product/${this.product.id}/reviews/`, {
                author: this.review.author,
                email: this.review.email,
                text: this.review.text,
                rate: this.review.rate
            }).then(({data}) => {
                this.product.reviews = data
                alert('Отзыв опубликован')
                this.review.author = ''
                this.review.email = ''
                this.review.text = ''
                this.review.rate = 5
            }).catch((error) => {
                const status = error?.response?.status
                const data = error?.response?.data
                let message = 'Ошибка при публикации отзыва'
                if (status === 403) {
                    message = 'Чтобы оставить отзыв, войдите в аккаунт'
                } else if (status === 400 && data && typeof data === 'object') {
                    message = Object.entries(data)
                        .map(([field, errors]) => field + ': ' + [].concat(errors).join(' '))
                        .join('\n')
                }
                alert(message)
            })
        },
        setActivePhoto(index) {
            this.activePhoto = index
        }
    },
    mounted () {
        this.getProduct();
    },
    data() {
        return {
            product : {},
            activePhoto: 0,
            count: 1,
            review: {
                author: '',
                email: '',
                text: '',
                rate: 5
            }
        }
    },
}