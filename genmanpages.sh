#!/bin/sh

rm -rf man
mkdir -p man/etcdctl2 man/etcdctl3
pushd man/etcdctl3
ETCDCTL_API=3 ../../$1/bin/etcdctl --help

# rename to etcdctl3...
for line in $(ls *.1); do mv $line $(echo $line | sed "s/etcdctl/etcdctl3/"); done

# rename refs
sed -i "s/\\\fBetcdctl\\\-/\\\fBetcdctl3\\\-/g" *.1

# stress ETCDCTL_API use
sed -i s"/^\\\fBetcdctl /\\\fBETCDCTL=3 etcdctl /" etcdctl3*.1

cd ../etcdctl2
../../$1/bin/etcdctl --help > etcdctl.1

for cmd in $(cat etcdctl.1 | grep "\fBetcdctl\\\-" | cut -d'-' -f2-3 | cut -d'(' -f1); do ../../$1/bin/etcdctl $cmd --help > etcdctl-$cmd.1; done

# rename to etcdctl2
for line in $(ls *.1); do mv $line $(echo $line | sed "s/etcdctl/etcdctl2/"); done

# rename refs
sed -i "s/\\\fBetcdctl\\\-/\\\fBetcdctl2\\\-/g" *.1

cd ..
mv etcdctl2/* .
mv etcdctl3/* .
rm -rf etcdctl2 etcdctl3
cp ../etcdctl.1 .

# Gen etcd.1
../$1/bin/etcd --help > etcd.1
