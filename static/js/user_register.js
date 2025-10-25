let vm = new Vue({
    el: '#app', //绑定app
    delimiters: ['[[', ']]'],
    data : {
        username:'',
        password:'',
        phone:'',
        resetpw:'',
        image_code_url: '',

        error_phone:false,
        error_name:false,
        error_password:false,
        error_resetpw:false,

        error_name_message:'',
        error_phone_message: ''

    },
    mounted(){
      this.image_code();
    },

    //定义的事件方法
    methods:{
    //    校验用户名数据
        image_code(){
            this.image_code_url ='/image/?' + new Date().getTime()
        },

        check_name(){
            //定义用户名的规则范围
            let re = /^[A-Za-z0-9_]{3,15}$/;
        //    判断用户名是否满足定义的规则
            if (re.test(this.username)){
            //    用户名合法
                this.error_name = false;
            } else {
            //    用户名不合法
                this.error_name = true;
                this.error_name_message = '用户名不合法'
            }
            if(this.error_name == false){
                // 发送ajax请求
                axios.get(
                    '/ucount/'+this.username,
                    {responseType:'json'}
                )
                    // 请求成功
                    .then(response => {
                        // 获取后端传递过来的数据
                        if(response.data.count > 0){
                            // 用户名存在
                            this.error_name = true;
                            this.error_name_message = '用户名已存在'
                        } else {
                            this.error_name = false;
                        }
                    })
                    // 请求失败
                    .catch(error => {
                        console.log(error.response)
                    })
            }
        },
    //    校验密码
        check_password() {
            let re = /^[A-Za-z0-9_]{6,15}$/;
            if (re.test(this.password)) {
                //    密码合法
                this.error_password = false;
            } else {
                //    密码不合法
                this.error_password = true;
            }
        },
        check_resetpw(){
            if(this.password == this.resetpw){
                this.error_resetpw = false;
            }else {
                this.error_resetpw = true;
            }
        },
        check_phone(){
            // 定义电话的规则范围
            let re = /^[0-9]{11}$/;
            if (re.test(this.phone)){
                this.error_phone = false;
            } else {
                this.error_phone = true;
                this.error_phone_message = '电话号格式有误'
            }
            if (this.error_phone == false){
                axios.get('/count/' + this.phone + '/',
                    {responseType: 'json'}
                )
                    .then(response => {
                        if (response.data.count > 0){
                            // 电话号存在
                            this.error_phone = true;
                            this.error_phone_message = '该电话号已绑定其他账号';
                        } else {
                            this.error_phone = false;
                        }
                    })
                    .catch(error =>{
                        console.log(error.response)
                    })
            }
        },
        on_submit(){
            this.check_name();
            this.check_password();
            this.check_resetpw();
            if(this.error_name ==true || this.error_password ==true ||this.resetpw==true){
                windows.event.returnValue = false;
            }
        }
    }
})