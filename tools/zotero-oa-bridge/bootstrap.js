var ZoteroOAPipelineBridge;

async function startup({ id, version, rootURI }, reason) {
  Services.scriptloader.loadSubScript(rootURI + "bridge.js");
  await ZoteroOAPipelineBridge.startup({ id, version, rootURI });
}

function shutdown({ id, version, rootURI }, reason) {
  if (ZoteroOAPipelineBridge) {
    ZoteroOAPipelineBridge.shutdown();
  }
}

function install() {}

function uninstall() {}
