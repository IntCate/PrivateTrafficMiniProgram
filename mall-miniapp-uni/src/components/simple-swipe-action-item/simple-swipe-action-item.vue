<template>
	<view class="simple-swipe">
		<view class="simple-swipe_box" :change:prop="wxsswipe.showWatch" :prop="is_show"
			:data-threshold="threshold" :data-disabled="disabled" @touchstart="wxsswipe.touchstart"
			@touchmove="wxsswipe.touchmove" @touchend="wxsswipe.touchend">
			<view class="simple-swipe_text--center">
				<slot></slot>
			</view>
			<view class="simple-swipe_button-group button-group--right">
				<view v-for="(item,index) in rightOptions" :key="index" :style="{
				  backgroundColor: item.style && item.style.backgroundColor ? item.style.backgroundColor : '#C7C6CD'
				}" class="simple-swipe_button button-hock" @touchstart.stop="appTouchStart"
					@touchend.stop="appTouchEnd($event,index,item,'right')" @click.stop="onClickForPC(index,item,'right')">
					<text class="simple-swipe_button-text"
						:style="{color: item.style && item.style.color ? item.style.color : '#FFFFFF',fontSize: item.style && item.style.fontSize ? item.style.fontSize : '16px'}">{{ item.text }}</text>
				</view>
			</view>
		</view>
	</view>
</template>
<script src="./swipe.wxs" module="wxsswipe" lang="wxs"></script>
<script>
	export default {
		name: 'simpleSwipeActionItem',
		emits: ['click', 'change'],
		props: {
			show: {
				type: String,
				default: 'none'
			},
			disabled: {
				type: Boolean,
				default: false
			},
			autoClose: {
				type: Boolean,
				default: true
			},
			threshold: {
				type: Number,
				default: 20
			},
			rightOptions: {
				type: Array,
				default () {
					return []
				}
			}
		},
		data() {
			return {
				is_show: 'none'
			}
		},
		watch: {
			show(newVal) {
				this.is_show = this.show
			}
		},
		created() {
			this.swipeaction = this.getSwipeAction()
			if (this.swipeaction && Array.isArray(this.swipeaction.children)) {
				this.swipeaction.children.push(this)
			}
			this.onCloseAllHandler = () => {
				this.close()
			}
			uni.$on('closeSwipeActionAll', this.onCloseAllHandler)
		},
		mounted() {
			this.is_show = this.show
			if (!this.swipeaction) {
				this.swipeaction = this.getSwipeAction()
				if (this.swipeaction && Array.isArray(this.swipeaction.children)) {
					this.swipeaction.children.push(this)
				}
			}
		},
		unmounted() {
			this.__isUnmounted = true
			uni.$off('closeSwipeActionAll', this.onCloseAllHandler)
			this.uninstall()
		},
		methods: {
			uninstall() {
				if (this.swipeaction) {
					this.swipeaction.children.forEach((item, index) => {
						if (item === this) {
							this.swipeaction.children.splice(index, 1)
						}
					})
				}
			},
			getSwipeAction(name = 'simpleSwipeAction') {
				let parent = this.$parent;
				let parentName = parent.$options.name;
				while (parentName !== name) {
					parent = parent.$parent;
					if (!parent) return false;
					parentName = parent.$options.name;
				}
				return parent;
			},
			closeSwipe(e) {
				if (this.autoClose && this.swipeaction) {
					this.swipeaction.closeOther(this)
				}
			},
			close() {
				this.is_show = 'none'
			},
			change(e) {
				this.$emit('change', e.open)
				if (this.is_show !== e.open) {
					this.is_show = e.open
				}
			},
			appTouchStart(e) {
				const {
					clientX
				} = e.changedTouches[0]
				this.clientX = clientX
				this.timestamp = new Date().getTime()
			},
			appTouchEnd(e, index, item, position) {
				const {
					clientX
				} = e.changedTouches[0]
				const diff = Math.abs(this.clientX - clientX)
				const time = (new Date().getTime()) - this.timestamp
				if (diff < 40 && time < 300) {
					this.$emit('click', {
						content: item,
						index,
						position
					})
					this.is_show = 'none'
				}
			},
			onClickForPC(index, item, position) {
				// #ifdef H5
				this.$emit('click', {
					content: item,
					index,
					position
				})
				// #endif
			}
		}
	}
</script>
<style>
	.simple-swipe {
		position: relative;
		overflow: hidden;
		border-radius: 12px;
		background-color: #FFFFFF;
		border: 1px solid #F2E8E2;
	}

	.simple-swipe_box {
		display: flex;
		flex-shrink: 0;
		position: relative;
	}

	.simple-swipe_text--center {
		width: 100%;
		background-color: #FFFFFF;
		border-radius: 12px;
		padding: 12px;
		box-sizing: border-box;
	}

	.simple-swipe_button-group {
		box-sizing: border-box;
		display: flex;
		flex-direction: row;
		position: absolute;
		top: 0;
		bottom: 0;
	}

	.button-group--right {
		right: 0;
		transform: translateX(100%)
	}

	.simple-swipe_button {
		display: flex;
		flex-direction: row;
		justify-content: center;
		align-items: center;
		padding: 0;
		width: 88px;
	}

	.simple-swipe_button-text {
		flex-shrink: 0;
		font-size: 14px;
	}

	.ani {
		transition-property: transform;
		transition-duration: 0.3s;
		transition-timing-function: cubic-bezier(0.165, 0.84, 0.44, 1);
	}
</style>