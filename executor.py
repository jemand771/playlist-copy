from model import Job, SizeAgeLimit, SourceMode, TargetDupeMode, TargetMode, User


def run_job(user: User, job: Job):
    # resolve target
    if job.target_mode == TargetMode.create:
        target = user.api.create_playlist()
    elif job.target_mode == TargetMode.existing:
        target = user.api.resolve_playlist(job.target)
    else:
        raise Exception("unexpected target mode:", job.target_mode)
    if job.purge_before_operation:
        target.purge(SizeAgeLimit(count=0))
    if job.src_mode in (SourceMode.copy, SourceMode.move):
        source = user.api.resolve_playlist(job.source)
        remove_from_source = []
        for i, item in enumerate(source.get_items(limit=job.fetch_limit, reverse=job.reverse_source)):
            if job.target_dupe_mode == TargetDupeMode.leave:
                if target.contains(item):
                    continue
            elif job.target_dupe_mode == TargetDupeMode.void:
                if target.contains(item):
                    remove_from_source.append(i)
                    continue
            elif job.target_dupe_mode == TargetDupeMode.include:
                if job.src_mode == SourceMode.move:
                    remove_from_source.append(i)
            target.add(item)
        for idx in reversed(remove_from_source):
            source.remove_at_index(idx)
    target.purge(job.purge_after_limit)
    # TODO implement seen as dupe
