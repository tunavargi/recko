var token = Cookies.get("token")
var nsfw = false;
var _id;
var signedUp = false;
if (!token) {
    $.post("/authenticate", {}).done(function(response) {
        response = JSON.parse(response)
        token = response.token;
        signedUp = Boolean(response.email);
        Cookies.set('token', token, {expires: 365 * 3});
        getter()
    })
}
else{
    getter()
}
var shortUrl = function(u) {
   uend = u.slice(u.length - 15);
   ustart = u.replace('http://', '').replace('https://', '').substr(0, 32);
   var shorter = ustart + '...' + uend;
   return shorter;
 }

function getter() {
    $.get("next", {
        token: token,
        nsfw: nsfw
    }, function (response) {
        _id = response.article.id;

        if (response.article.content.startsWith("http")) {
            $("#embed").html("<img height=80% src=" + response.article.content + "></img>");
        }
        else {
            $("#embed").html(response.article.content);
            $("#title").html(response.article.title);
        }
        $("#url").html('<a href="' + response.article.url + '">' + shortUrl(response.article.url)+ '</a>')
    }).fail(function (response) {
        if (response.status == 403){
        $.removeCookie("token")
    }})
}

var like = function(){
 var data = JSON.stringify({url: _id});

 $.ajax({type: 'POST',
         url: '/like?token=' + token,
         data: data,
         contentType: "application/json",
         dataType: "application/json",
         complete: function (response) {
            getter()
        }
        });

};
$(".like").on("click", function(){like()});
$(".next").on("click", function(){
    getter()
});
$(document).keydown(function(e) {
    switch(e.which) {
        case 37: // left
            getter()
            break;
        case 39: // right
            like();
}})
