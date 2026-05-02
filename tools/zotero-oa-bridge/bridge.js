var ZoteroOAPipelineBridge = {
  endpoint: "/oa-pipeline/find-files",

  async startup() {
    Zotero.debug("OA Pipeline Bridge starting");
    Zotero.Server.Endpoints[this.endpoint] = this.Endpoint;
  },

  shutdown() {
    Zotero.debug("OA Pipeline Bridge shutting down");
    if (Zotero.Server && Zotero.Server.Endpoints) {
      delete Zotero.Server.Endpoints[this.endpoint];
    }
  },

  Endpoint: function () {},

  async processItem(data) {
    let item = new Zotero.Item("journalArticle");
    item.libraryID = Zotero.Libraries.userLibraryID;
    if (data.title) item.setField("title", data.title);
    if (data.doi) item.setField("DOI", data.doi);
    if (data.url) item.setField("url", data.url);
    if (data.year) item.setField("date", data.year);
    if (data.journal) item.setField("publicationTitle", data.journal);
    if (data.row_id) item.setField("extra", `oa_pipeline_row_id: ${data.row_id}`);
    if (Array.isArray(data.creators) && data.creators.length) {
      item.setCreators(data.creators.map((creator) => ({
        firstName: creator.firstName || creator.first_name || "",
        lastName: creator.lastName || creator.last_name || creator.name || "",
        creatorType: creator.creatorType || "author"
      })));
    }
    await item.saveTx();

    let lookupError = "";
    let directResult = false;
    try {
      directResult = await Zotero.Attachments.addAvailableFile(item, {
        methods: ["doi", "url", "oa", "custom"]
      });
    }
    catch (e) {
      lookupError = e && e.message ? e.message : String(e);
      Zotero.logError(e);
    }

    let attachments = [];
    for (let attachmentID of item.getAttachments()) {
      let attachment = Zotero.Items.get(attachmentID);
      if (!attachment) continue;
      let path = false;
      try {
        path = await attachment.getFilePathAsync();
      }
      catch (e) {
        Zotero.logError(e);
      }
      attachments.push({
        item_id: attachment.id,
        item_key: attachment.key,
        title: attachment.getField("title"),
        content_type: attachment.attachmentContentType || "",
        path: path || "",
        url: attachment.getField("url") || ""
      });
    }

    return {
      row_id: data.row_id || "",
      item_id: item.id,
      item_key: item.key,
      title: item.getField("title"),
      doi: item.getField("DOI"),
      url: item.getField("url"),
      direct_result: !!directResult,
      lookup_error: lookupError,
      attachments
    };
  }
};

ZoteroOAPipelineBridge.Endpoint.prototype = {
  supportedMethods: ["POST"],
  supportedDataTypes: ["application/json"],
  permitBookmarklet: false,

  async init(requestData) {
    let data = requestData.data || {};
    let items = Array.isArray(data.items) ? data.items : [];
    let results = [];
    for (let item of items) {
      try {
        results.push(await ZoteroOAPipelineBridge.processItem(item));
      }
      catch (e) {
        Zotero.logError(e);
        results.push({
          row_id: item && item.row_id || "",
          error: e && e.message ? e.message : String(e),
          attachments: []
        });
      }
    }
    return [200, "application/json", JSON.stringify({
      ok: true,
      count: results.length,
      results
    })];
  }
};
