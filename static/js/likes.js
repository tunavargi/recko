    var shortUrl = function(u) {
       uend = u.slice(u.length - 15);
       ustart = u.replace('http://', '').replace('https://', '').substr(0, 42);
       var shorter = ustart + '...' + uend;
       return shorter;
     }

    var token = Cookies.get("token")
    $.get("/likes?token=" + token, function(response){
        response = JSON.parse(response);
        response.articles.forEach(function(item){
            item_info = item.title ? item.title : shortUrl(item.url);
            var like = ('<div class="link-small" id="title">' +
                                '<a target="_blank" href="' + item.url + '">'+ item_info +'</a>' +
                             '</div>');
            console.log(like)
            $(".row").append(like);
        })
    });