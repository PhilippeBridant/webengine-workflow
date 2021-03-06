/* Compute failed/success/not_solved/mine item total */

function compute_total_items_state() {
    gl_not_solved = $("div.categories_table_workflow td.state-item-None").length;
    gl_success = $("div.categories_table_workflow td.state-item-OK").length;
    gl_failed = $("div.categories_table_workflow td.state-item-KO").length;
    gl_total = gl_success + gl_failed + gl_not_solved;
    update_statistics_progressbar();
    $("#progress_bar").html(progressbar);
    gl_total = gl_taken + gl_untaken;
    update_statistics_filters();
}

/* ***************** */

/* Compute taken/untaken item total */

function compute_taken_untaken_items() {
    var untaken_item_cel = $("div.categories_table_workflow").find(".category_workflow td.take-item");
    var taken_item_cel = $("div.categories_table_workflow").find(".category_workflow td.untake-item");
    gl_taken = taken_item_cel.length;
    gl_untaken = untaken_item_cel.length;
    update_statistics_filters();
}

/* ***************** */

/* Update actions shortcut items */

function  _update_item_shortcut(data, link, el) {
    link = link.split('/');
    if ($(el).hasClass("shortcut-disabled-None")) {
	link[link.length - 1] = "OK/";
	var ok_shortcut = "<a class='shortcut-disabled-OK shortcut' href=" + link.join('/').replace("/no_state/", "/validate/");
	ok_shortcut += " title='Click to validate'><img src='/medias/workflow/img/validation_OK_disabled.png'/></a>";
	var no_state_shortcut = "<a title='Item is untested'> ? </a>";
	link[link.length - 1] = "KO/";
	var ko_shortcut = "<a class='shortcut-disabled-KO shortcut' href='" + link.join('/').replace("/no_state/", "/validate/");
	ko_shortcut += "' title='Click to mark as broken'><img src='/medias/workflow/img/validation_KO_disabled.png'/></a>";
	$(el).parent().attr("class", "state-item-None");
    } else {
	if ($(el).hasClass("shortcut-disabled-KO")) {
		link[link.length - 2] = "OK";
		var ok_shortcut = "<a class='shortcut-disabled-OK shortcut' href='" + link.join('/');
		ok_shortcut += "' title='Click to validate'><img src='/medias/workflow/img/validation_OK_disabled.png'/></a>";
		var ko_shortcut = "<a class='shortcut-enabled-KO' title='Item is broken'>";
		ko_shortcut += "<img src='/medias/workflow/img/validation_KO.png'/></a>";
		$(el).parent().attr("class", "state-item-KO");
	} else {
		link[link.length - 2] = "KO";
		var ko_shortcut = "<a class='shortcut-disabled-KO shortcut' href='" + link.join('/');
		ko_shortcut += "' title='Click to mark as broken'><img src='/medias/workflow/img/validation_KO_disabled.png'/></a>";
		var ok_shortcut = "<a class='shortcut-enabled-KO shortcut' title='Item is validated'>";
		ok_shortcut += "<img src='/medias/workflow/img/validation_OK.png'/></a>";
		$(el).parent().attr("class", "state-item-OK");
	}
	link[link.length - 2] = '';
	link[link.length - 1] = '';
	var no_state_shortcut = "<a class='shortcut-disabled-None shortcut' href='" + link.join('/').replace('validate', 'no_state');
	no_state_shortcut += "' title='Reset item validation'> ? </a>";
    }
    if ($("span#action_shortcuts").html()) {
	$("span#action_shortcuts").html(ok_shortcut + no_state_shortcut + ko_shortcut);
    } else {
	$(el).parent().html(ok_shortcut + no_state_shortcut + ko_shortcut);
	compute_total_items_state();
    }
}

function update_item_shortcut() {
    link = $(this).attr("href");
    item_has_changed(this, link, _update_item_shortcut);
    return false;
}

/* ***************** */

/* Take one item */

function _update_item_add_owner(data, link, el) {
    var href = $(el).find("a").attr("href").replace("/take/", "/untake/");
    var content = data["assigned_to_firstname"] + " " + data["assigned_to_lastname"].toUpperCase();
    content += " <a href='" + href + "' title='Untake item'><img src='/medias/workflow/img/untake.png' /></a>";
    $(el).attr("class", "untake-item owner-" + data["assigned_to"]).html(content);
    $(el).attr("id", "untake-item-" + data["item_id"]);
    compute_taken_untaken_items();
}

function update_item_add_owner() {
    link = $(this).find("a").attr("href");
    item_has_changed(this, link, _update_item_add_owner);
    return false;
}

/* ***************** */

/* Untake one item */

function _update_item_reset_owner(data, link, el) {
    var href = $(el).find("a").attr("href").replace("/untake/", "/take/");
    var content = "<a href='" + href + "' title='Take item'>take</a>";
    $(el).attr("class", "take-item owner-None").html(content);
    $(el).attr("id", "take-item-" + data["item_id"]);
    compute_taken_untaken_items();
}

function update_item_reset_owner() {
    link = $(this).find("a").attr("href");
    item_has_changed(this, link, _update_item_reset_owner);
    return false;
}

/* ***************** */

/* Untake a whole group */

function _update_whole_group_reset_owner(data) {
    var element_to_add = $("table#category_id-" + data["category_id"] + " td.untake-item");
      for (var i = 0; i < element_to_add.length ; i++) {
	  data["item_id"] = $(element_to_add[i]).attr("id").split('-')[2];
	  _update_item_reset_owner(data, null, element_to_add[i]);
    }
}

function update_whole_group_reset_owner() {
    link = $(this).attr("href");
    $.ajax({
    url: link,
    type: "POST",
    dataType: "json",
    timeout: 3000,
    success: function(data, textStatus, jqXHR) { _update_whole_group_reset_owner(data); },
    error: function(XMLHttpRequest, textStatus, errorThrown) { alert(error_message); },
    });
    return false;
}

/* ***************** */

/* Take a whole group */

function _update_whole_group_add_owner(data) {
    var element_to_add = $("table#category_id-" + data["category_id"] + " td.take-item");
      for (var i = 0; i < element_to_add.length ; i++) {
	  data["item_id"] = $(element_to_add[i]).attr("id").split('-')[2];
	  _update_item_add_owner(data, null, element_to_add[i]);
    }
}


function update_whole_group_add_owner() {
    link = $(this).attr("href");
    $.ajax({
    url: link,
    type: "POST",
    dataType: "json",
    timeout: 3000,
    success: function(data, textStatus, jqXHR) { _update_whole_group_add_owner(data); },
    error: function(XMLHttpRequest, textStatus, errorThrown) { alert(error_message); },
    });
    return false;
}

/* ***************** */
var error_message = "Errors unexpectedly happened. Please refresh the page."
