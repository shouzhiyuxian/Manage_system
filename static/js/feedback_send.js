 function toggleFeedbackList(type) {
            const getList = document.getElementById('feedback_get_list');
            const sendList = document.getElementById('feedback_send_list');

            if (type === 'get') {
                getList.style.display = 'block';
                sendList.style.display = 'none';
            } else if (type === 'send') {
                getList.style.display = 'none';
                sendList.style.display = 'block';
            }
        }