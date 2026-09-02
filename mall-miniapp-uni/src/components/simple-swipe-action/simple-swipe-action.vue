<template>
	<view>
		<slot></slot>
	</view>
</template>

<script>
	export default {
		name: "simpleSwipeAction",
		created() {
			this.children = [];
		},
		methods: {
			closeAll() {
				this.children.forEach(vm => {
					if (!vm) return
					vm.is_show = 'none'
				})
			},
			closeOther(vm) {
				if (this.openItem && this.openItem !== vm) {
					this.openItem.is_show = 'none'
				}
				this.openItem = vm
			}
		}
	};
</script>