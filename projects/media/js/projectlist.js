var ProjectList = function (config) {
    var self = this;
    self.template_label = config.template_label;
    self.parent = config.parent;
    self.switcher_context = {};
    
    // add some flair to the collection table
    jQuery(self.parent).find(".collection_table").ajaxStart(function () {
        jQuery(this).addClass("ajaxLoading");
    });
    
    jQuery(self.parent).find(".collection_table").ajaxStop(function () {
        jQuery(this).removeClass("ajaxLoading");
    });
    
    jQuery.ajax({
        url: '/site_media/templates/' + config.template + '.mustache?nocache=v2',
        dataType: 'text',
        cache: false, // Chrome && Internet Explorer has aggressive caching policies.
        success: function (text) {
            MediaThread.templates[config.template] = Mustache.template(config.template, text);
            
            var url = null;
            
            self.refresh(config);
        }
    });
    
    return this;
};

ProjectList.prototype.refresh = function (config) {
    var self = this;
    var url;
    
    // Retrieve the full asset w/annotations from storage
    if (config.view === 'all' || !config.space_owner) {
        url = MediaThread.urls['all-projects']();
    } else {
        url = MediaThread.urls['your-projects'](config.space_owner);
    }
    
    djangosherd.storage.get({
        type: 'asset',
        url: url
    },
    false,
    function (the_records) {
        self.updateAssets(the_records);
    });
};

ProjectList.prototype.selectOwner = function (username) {
    var self = this;
    djangosherd.storage.get({
        type: 'asset',
        url: username ? MediaThread.urls['your-space'](username, null, null, self.citable) : MediaThread.urls['all-space'](null, null, self.citable)
    },
    false,
    function (the_records) {
        self.updateAssets(the_records);
    });
    
    return false;
};

ProjectList.prototype.clearFilter = function (filterName) {
    var self = this;
    var active_tag = null;
    var active_modified = null;
        
    if (filterName === 'tag') {
        active_modified = ('modified' in self.current_records.active_filters) ? self.current_records.active_filters.modified : null;
    } else if (filterName === 'modified') {
        active_tag = ('tag' in self.current_records.active_filters) ? self.current_records.active_filters.tag : null;
    }
    
    djangosherd.storage.get({
        type: 'asset',
        url: self.getSpaceUrl(active_tag, active_modified)
    },
    false,
    function (the_records) {
        self.updateAssets(the_records);
    });
    
    return false;
};

ProjectList.prototype.getShowingAllItems = function (json) {
    return !json.hasOwnProperty('space_owner');
};

ProjectList.prototype.getSpaceUrl = function (active_tag, active_modified) {
    var self = this;
    if (self.getShowingAllItems(self.current_records)) {
        return MediaThread.urls['all-space'](active_tag, active_modified, self.citable);
    } else {
        return MediaThread.urls['your-space'](self.current_records.space_owner.username, active_tag, active_modified, self.citable);
    }
};

ProjectList.prototype.updateSwitcher = function () {
    var self = this;
    self.switcher_context.display_switcher_extras = !self.switcher_context.showing_my_items || (self.current_project && self.current_project.participants.length > 1);
    Mustache.update("switcher_collection_chooser", self.switcher_context, { parent: self.parent });
    
    // hook up switcher choice owner behavior
    jQuery(self.parent).find("a.switcher-choice.owner").unbind('click').click(function (evt) {
        var srcElement = evt.srcElement || evt.target || evt.originalTarget;
        var bits = srcElement.href.split("/");
        var username = bits[bits.length - 1];
        
        if (username === "all-class-members") {
            username = null;
        }
        return self.selectOwner(username);
    });

};

ProjectList.prototype.updateAssets = function (the_records) {
    var self = this;
    self.switcher_context.owners = the_records.owners;
    self.switcher_context.space_viewer = the_records.space_viewer;
    self.switcher_context.selected_view = self.selected_view;
    
    if (self.getShowingAllItems(the_records)) {
        self.switcher_context.selected_label = "All Class Members";
        self.switcher_context.showing_all_items = true;
        self.switcher_context.showing_my_items = false;
        the_records.showing_all_items = true;
    } else if (the_records.space_owner.username === the_records.space_viewer.username) {
        self.switcher_context.selected_label = "Me";
        self.switcher_context.showing_my_items = true;
        self.switcher_context.showing_all_items = false;
        the_records.showing_my_items = true;
    } else {
        self.switcher_context.showing_my_items = false;
        self.switcher_context.showing_all_items = false;
        self.switcher_context.selected_label = the_records.space_owner.public_name;
    }
    
    self.current_records = the_records;
    
    var n = _propertyCount(the_records.active_filters);
    if (n > 0) {
        the_records.active_filter_count = n;
    }
    
    Mustache.update(self.template_label, the_records, {
        parent: self.parent,
        pre: function (elt) { jQuery(elt).hide(); },
        post: function (elt) {
            self.updateSwitcher();
            
            jQuery(elt).fadeIn("slow");
            
            jQuery(self.parent).find("a.switcher-choice.remove").unbind('click').click(function (evt) {
                var href = jQuery(this).attr("href");
                var bits = href.split("/");
                var filterName = bits[bits.length - 1];
                
                if (filterName === "both") {
                    filterName = null;
                }
                return self.clearFilter(filterName);
            });
        }
    });
};
    