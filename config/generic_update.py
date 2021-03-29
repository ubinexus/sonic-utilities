class JsonChange:
    pass

class PatchOrderer:
    def order(patch):
        pass

class ChangeApplier:
    def apply(change):
        pass

class PatchApplier:
    def apply(self, patch, format, verbose, dry_run):
        pass

class ConfigReplacer:
    def replace(self, full_json, format, verbose, dry_run):
        pass

class FileSystemRollbacker:
    def checkpoint(self, checkpoint_name, format, verbose, dry_run):
        pass
    def rollback(self, checkpoint_name, format, verbose, dry_run):
        pass



