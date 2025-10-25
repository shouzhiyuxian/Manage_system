let map;
let marker;
let studentId = '12345'; // 假设这是学生的ID，可以从服务器获取或通过其他方式传递
let address_info = ''

function initMap(position) {
    map = new BMapGL.Map("map");
    const point = new BMapGL.Point(position.lng, position.lat); // 使用定位的位置作为中心点
    map.centerAndZoom(point, 15);
    map.enableScrollWheelZoom(true);

    marker = new BMapGL.Marker(point);
    map.addOverlay(marker);
    map.panTo(point);
    document.getElementById('loading').style.display = 'none';
}

function getCurrentPosition() {
    var geolocation = new BMapGL.Geolocation();
    geolocation.enableSDKLocation();
    geolocation.getCurrentPosition(function (r) {
        if (this.getStatus() == BMAP_STATUS_SUCCESS) {
            var pos = r.point;

            initMap({ lng: pos.lng, lat: pos.lat });
            map.centerAndZoom(new BMapGL.Point(pos.lng,pos.lat), 11);
        // 创建地理编码实例
            var myGeo = new BMapGL.Geocoder();
            // 根据坐标得到地址描述
            myGeo.getLocation(new BMapGL.Point(pos.lng,pos.lat), function(result){
                if (result){
                  address_info = result.address
                }
            });
        } else {
            document.getElementById('status').innerText = '无法获取当前位置，请稍后再试。';
        }
    });
}

// 添加签到按钮的事件监听器
const signinButton = document.getElementById('signinButton');
if (signinButton) {
    signinButton.addEventListener('click', function () {
        if (marker) {
            const location = marker.getPosition();
            fetch('/position_signin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    student_id: studentId,
                    latitude: location.lat,
                    longitude: location.lng,
                    address_info: address_info,
                })
            }).then(response => response.json())
              .then(data => {
                  if (data.status === 'success') {
                      alert('签到成功！位置为' + address_info)
                  } else {
                      alert('签到失败,' + data.status)
                  }
              }).catch(error => {
                  console.error('签到请求失败:', error);
                  alert('签到请求失败，请检查网络连接。')
              });
        } else {
            alert('无法获取当前位置，请稍后再试。')
        }
    });
} else {
    console.error('签到按钮未找到');
}

// 调用getCurrentPosition函数来获取当前位置并初始化地图
getCurrentPosition();
